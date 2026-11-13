"""Stage workers run in the existing isolated model environments."""
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from scene_pipeline import ROOT, call, probe, sha, write

def done(run, stage, files, **extra):
    write(run/f'{stage}.done.json', {'outputs':{str(Path(f).relative_to(run)):sha(f) for f in files},**extra})

def np_sf():
    import numpy as np
    import soundfile as sf
    return np,sf

def mono(x): return x.mean(axis=1) if x.ndim>1 else x

def substitution(source,target):
    # Keep shared delivery punctuation outside the replacement tag.
    a=re.match(r'^(.*?)([.!?]+)$',source,flags=re.S)
    b=re.match(r'^(.*?)([.!?]+)$',target,flags=re.S)
    if a and b and a[2]==b[2]:
        return f'<sub targ="{html.escape(b[1],quote=True)}">{html.escape(a[1])}</sub>{a[2]}'
    return f'<sub targ="{html.escape(target,quote=True)}">{html.escape(source)}</sub>'

def separate(run,c):
    from audio_separator.separator import Separator
    np,sf=np_sf()
    sep=Separator(output_dir=str(run/'separation'),output_format='WAV',model_file_dir=str(ROOT/'models/separation'),sample_rate=48000)
    sep.load_model(c['settings']['separator_model']);outputs=sep.separate(str(run/'dialogue-input.wav'))
    candidates=[run/'separation'/Path(x).name for x in outputs if '(Vocals)' in Path(x).name]
    if len(candidates)!=1:raise RuntimeError(f'Expected one Vocals stem, got {outputs}')
    y,sr=sf.read(candidates[0]);assert sr==48000
    sf.write(run/'foreground.wav',mono(y),sr,subtype='PCM_24')

def prepare(run,c,p):
    np,sf=np_sf();source=c['source'];clip=run/'source.mkv'
    args=['ffmpeg','-v','error','-y','-i',source['path']]
    trimmed=bool(source.get('start',0) or source.get('end') is not None)
    if trimmed:args+=['-ss',str(p['source_start']),'-t',str(p['duration'])]
    args+=['-map','0:v:0','-map','0:a:0']
    args+=['-c:v','libx264','-crf','16','-preset','fast','-r',p['fps'],'-fps_mode','cfr'] if trimmed else ['-c:v','copy']
    args+=['-c:a','pcm_s24le','-ar','48000',str(clip)];call(args)
    wav=run/'original.wav';call(['ffmpeg','-v','error','-y','-i',clip,'-map','0:a:0','-c:a','pcm_s24le',wav])
    x,sr=sf.read(wav,always_2d=True);assert sr==48000
    stream=next(s for s in probe(clip)['streams'] if s['codec_type']=='video')
    # Frame count via decoding works for MKV, whose nb_frames is commonly absent.
    counted=json.loads(call(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames','-of','json',clip]))
    frames=int(counted['streams'][0]['nb_read_frames'])
    if frames<=0:raise RuntimeError('Cannot determine source frame count')
    for q in c['cues']:
        if round(q['end']*sr)>len(x):raise ValueError(f'Cue {q["id"]} exceeds extracted PCM')
    sf.write(run/'dialogue-input.wav',x[:,p['dialogue_channels']].mean(axis=1),sr,subtype='PCM_24')
    if source.get('foreground'):
        y,ys=sf.read(source['foreground']);y=mono(y)
        if ys!=sr:
            import librosa
            y=librosa.resample(y,orig_sr=ys,target_sr=sr)
        a=round(p['source_start']*sr);y=y[a:a+len(x)]
        if len(y)!=len(x):raise ValueError('Supplied foreground must align with full source timeline and cover the extracted clip')
        sf.write(run/'foreground.wav',y,sr,subtype='PCM_24')
    else:
        python=c['tools']['separate']
        call([python,Path(__file__).resolve(),'separate',run],run/'separate.log')
    y,ys=sf.read(run/'foreground.wav');assert ys==sr
    if len(y)<len(x):y=np.pad(y,(0,len(x)-len(y)))
    sf.write(run/'foreground.wav',y[:len(x)],sr,subtype='PCM_24')
    write(run/'media.json',dict(frames=frames,fps=p['fps'],width=stream['width'],height=stream['height'],samples=len(x),sample_rate=sr,channels=x.shape[1],dialogue_channels=p['dialogue_channels'],trim_reencoded_video=trimmed))
    done(run,'prepare',[clip,wav,run/'dialogue-input.wav',run/'foreground.wav',run/'media.json'])

def generate(run,c,p):
    np,sf=np_sf();s=c['settings'];sr=48000
    center,_=sf.read(run/'dialogue-input.wav');fore,_=sf.read(run/'foreground.wav')
    runtime=None
    if any(not q.get('take') for q in c['cues']):
        from dots_tts.edit_runtime import DotsTtsEditRuntime
        from dots_tts.utils.util import seed_everything
        runtime=DotsTtsEditRuntime.from_pretrained(s['model'],precision=s['precision'],max_generate_length=s['max_generate_length'],max_sequence_length=s['max_sequence_length'],optimize=False)
    files=[];records=[]
    for q in c['cues']:
        folder=run/'takes'/q['id'];folder.mkdir(parents=True,exist_ok=True)
        source=folder/'performance.wav';conditioning=q.get('conditioning',s['conditioning'])
        if conditioning not in ['foreground','original']:raise ValueError('conditioning must be foreground or original')
        y=(fore if conditioning=='foreground' else center)[round(q['start']*sr):round(q['end']*sr)]
        sf.write(source,y,sr,subtype='PCM_24');files.append(source)
        takes=[]
        if q.get('take'):
            spec=q['take'];y,ys=sf.read(spec['path']);y=mono(y)
            if spec.get('crop'):
                a,b=spec['crop']
                if a<0 or b<=a or round(b*ys)>len(y):raise ValueError('Invalid supplied take crop')
                y=y[round(a*ys):round(b*ys)]
            if ys!=sr:
                import librosa
                y=librosa.resample(y,orig_sr=ys,target_sr=sr)
            path=folder/'provided.wav';sf.write(path,y,sr,subtype='PCM_24');takes=[dict(path=str(path),seed=None)]
            selected=str(path)
        else:
            seeds=q.get('seeds',s['seeds']);selected_seed=q.get('selected_seed',seeds[0])
            instruction=q.get('instruction',substitution(q['source_text'],q['target_text']))
            for seed in seeds:
                path=folder/f'seed-{seed}.wav';seed_everything(seed)
                result=runtime.generate_edit(source_audio_path=str(source),instruction=instruction,source_text=q['source_text'],target_text=q['target_text'],use_xvector=True,speaker_scale=s['speaker_scale'])
                y=result['audio'].detach().float().cpu().squeeze().numpy();rate=result['sample_rate']
                if not y.size or not np.isfinite(y).all():raise RuntimeError('Invalid generated audio')
                if rate!=sr:raise RuntimeError(f'Unexpected model sample rate {rate}')
                sf.write(path,y,sr,subtype='PCM_24');takes.append(dict(path=str(path),seed=seed,instruction=instruction))
            selected=str(folder/f'seed-{selected_seed}.wav')
        files += [Path(t['path']) for t in takes]
        records.append(dict(id=q['id'],speaker=q['speaker'],performance=str(source),conditioning=conditioning,target_text=q['target_text'],takes=takes,selected=selected))
        print(q['id'],selected,flush=True)
    write(run/'takes.json',records);files.append(run/'takes.json');done(run,'generate',files)

def normalize(text):return ' '.join(re.findall(r'\w+',text.casefold()))

def check(run,c,p):
    enabled=c['settings']['check_words'];model=None;records=[];failures=[]
    if enabled:
        from transformers import pipeline
        model=pipeline('automatic-speech-recognition',model=c['settings']['asr_model'],device=0)
    for q in json.loads((run/'takes.json').read_text()):
        for t in q['takes']:
            result=model(t['path'],return_timestamps='word') if enabled else {'text':None,'chunks':[]}
            matches=normalize(result['text'])==normalize(q['target_text']) if enabled else None
            item=dict(id=q['id'],path=t['path'],selected=t['path']==q['selected'],matches=matches,asr=result)
            records.append(item)
            if item['selected'] and matches is False:failures.append(q['id'])
    write(run/'word-check.json',records)
    if failures:raise RuntimeError(f'Selected takes failed word checks for {failures}. Review check.log/word-check.json, select a different seed/take in the manifest, and rerun. ASR is fallible; check_words=false is an explicit override.')
    done(run,'check',[run/'word-check.json'],word_check_enabled=enabled,human_review='pending')

def active_rms(x,sr):
    import numpy as np
    window=round(.02*sr);energy=np.array([np.sqrt(np.mean(x[i:i+window]**2)) for i in range(0,len(x),window)])
    if not energy.size or energy.max()<1e-8:raise ValueError('No usable speech energy; review source/take')
    active=energy[energy>max(.0001,energy.max()*.1)]
    if not active.size:raise ValueError('Speech below RMS floor; review source/take')
    return float(np.sqrt(np.mean(active**2)))

def mix(run,c,p):
    np,sf=np_sf();import librosa
    s=c['settings'];original,sr=sf.read(run/'original.wav',always_2d=True);mixed=original.copy();driver=np.zeros(len(original));fore,_=sf.read(run/'foreground.wav');mask=np.zeros(len(original),bool)
    takes={q['id']:q for q in json.loads((run/'takes.json').read_text())};checks=json.loads((run/'word-check.json').read_text());records=[];files=[]
    for q in c['cues']:
        path=takes[q['id']]['selected'];y,ys=sf.read(path);assert ys==sr;y=mono(y)
        info=next(x for x in checks if x['id']==q['id'] and x['selected']);chunks=info['asr']['chunks']
        if chunks:
            left=max(0,(chunks[0]['timestamp'][0] or 0)-.035);right=min(len(y)/sr,(chunks[-1]['timestamp'][1] or len(y)/sr)+.035)
            y=y[round(left*sr):round(right*sr)]
        y,_=librosa.effects.trim(y,top_db=s['trim_db'],frame_length=512,hop_length=128)
        a,b=round(q['start']*sr),round(q['end']*sr);ov=fore[a:b]
        _,oi=librosa.effects.trim(ov,top_db=24,frame_length=512,hop_length=128)
        onset=int(oi[0])+round(q.get('onset_shift_seconds',0)*sr)
        if onset<0 or onset>=b-a:raise ValueError(f'Invalid onset in {q["id"]}')
        available=(b-a-onset)/sr-.025
        if available<=0:raise ValueError('No room for replacement')
        tempo=max(1,len(y)/sr/available);limit=q.get('tempo_limit',s['max_tempo'])
        if tempo>limit:raise ValueError(f'{q["id"]} needs tempo {tempo:.4f}, above {limit}. Retry, select another take or explicitly raise tempo_limit after auditioning.')
        selected=run/'selected';selected.mkdir(exist_ok=True);raw=selected/f'{q["id"]}-raw.wav';timed=selected/f'{q["id"]}-timed.wav'
        sf.write(raw,y,sr,subtype='PCM_24')
        if tempo>1:
            call(['ffmpeg','-v','error','-y','-i',raw,'-af',f'rubberband=tempo={tempo}:transients=smooth:detector=soft:phase=laminar:window=long:smoothing=on:formant=preserved','-c:a','pcm_s24le',timed])
        else:shutil.copyfile(raw,timed)
        y,_=sf.read(timed);gain=q.get('gain',active_rms(ov,sr)/active_rms(y,sr));y=y*gain
        if len(y)>b-a-onset:raise ValueError('Timed word exceeds slot; refusing to truncate speech')
        replacement=np.zeros(b-a);replacement[onset:onset+len(y)]=y
        gate=np.zeros(b-a);handle=round(s['handle_ms']*sr/1000);l=max(0,onset-handle);rr=min(b-a,max(int(oi[1]),onset+len(y))+handle);gate[l:rr]=1
        fade=min(round(s['fade_ms']*sr/1000),(rr-l)//2)
        if fade:gate[l:l+fade]=np.linspace(0,1,fade);gate[rr-fade:rr]=np.linspace(1,0,fade)
        for channel in p['dialogue_channels']:mixed[a:b,channel]+=gate*(replacement-ov)
        driver[a:b]=gate*replacement;mask[a:b]|=gate>0
        records.append(dict(id=q['id'],path=path,tempo=tempo,gain=float(gain),onset_seconds=onset/sr,source_onset_seconds=int(oi[0])/sr,channels=p['dialogue_channels']))
        files += [raw,timed]
    assert np.array_equal(original[~mask],mixed[~mask])
    untouched=[x for x in range(original.shape[1]) if x not in p['dialogue_channels']]
    assert np.array_equal(original[:,untouched],mixed[:,untouched])
    for a,b in c.get('protected_audio',[]):assert np.array_equal(original[round(a*sr):round(b*sr)],mixed[round(a*sr):round(b*sr)])
    if not np.isfinite(mixed).all() or np.max(abs(mixed))>=1:raise ValueError('Mix clips or contains invalid samples; adjust selected take gain')
    sf.write(run/'soundtrack.wav',mixed,sr,subtype='PCM_24');sf.write(run/'dialogue-driver.wav',driver,sr,subtype='PCM_24')
    call(['ffmpeg','-v','error','-y','-i',run/'source.mkv','-i',run/'soundtrack.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a',s['audio_bitrate'],'-movflags','+faststart',run/'original-picture.mp4'])
    write(run/'mix-receipt.json',dict(cues=records,unaffected_samples_equal=True,untouched_channels=untouched,protected_audio_equal=True,foreground_recovery='approximate within speech masks',human_review='pending'))
    done(run,'mix',files+[run/x for x in ['soundtrack.wav','dialogue-driver.wav','original-picture.mp4','mix-receipt.json']])

def lips(run,c,p):
    import cv2
    import numpy as np
    s=c['settings'];media=json.loads((run/'media.json').read_text());fps=Fraction(media['fps']);total=media['frames'];jobs=[];files=[]
    ff=ROOT/'facefusion';work=run/'lips';work.mkdir(exist_ok=True)
    # Every new stage invocation regenerates proposals. Only a fully hash-verified
    # completed stage is reused by the orchestrator.
    for q in c['cues']:
        for i,lip in enumerate(q['lips']):
            a=math.ceil(lip['start']*float(fps));b=min(total,math.floor(lip['end']*float(fps)))
            if b<=a:raise ValueError('Lip interval shorter than a complete video frame')
            if any(a<j['b'] and b>j['a'] for j in jobs):raise ValueError('Overlapping lip jobs after frame rounding')
            prefix=work/f'{q["id"]}-{i}';target=Path(str(prefix)+'-target.mp4');voice=Path(str(prefix)+'-driver.wav');proposal=Path(str(prefix)+'-proposal.mp4')
            call(['ffmpeg','-v','error','-y','-i',run/'source.mkv','-vf',f'trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS','-an','-c:v','libx264','-crf','16','-preset','veryfast',target])
            call(['ffmpeg','-v','error','-y','-ss',str(a/float(fps)),'-i',run/'dialogue-driver.wav','-t',str((b-a)/float(fps)),'-ac','1',voice])
            cmd=[c['tools']['lips'],ff/'local_run.py','headless-run','-s',voice,'-t',target,'-o',proposal,'--execution-providers','cuda','--processors','lip_syncer','--lip-syncer-model',s['mouth_model'],'--lip-syncer-weight',str(s['mouth_weight']),'--face-selector-mode','one','--face-selector-order',lip['face_order'],'--output-video-quality','95','--output-video-preset','fast','--execution-thread-count','4']
            call(cmd,Path(str(prefix)+'.log'))
            cap=cv2.VideoCapture(str(proposal));count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));cap.release()
            if count!=b-a:raise ValueError('Lip proposal frame count mismatch')
            jobs.append(dict(id=q['id'],a=a,b=b,order=lip['face_order'],proposal=str(proposal)));files += [target,voice,proposal]
    if jobs:
        import onnxruntime as ort
        dll=ROOT/'chatterbox/.venv/Lib/site-packages/torch/lib';handle=os.add_dll_directory(str(dll));ort.preload_dlls(directory=str(dll));sys.path.insert(0,str(ff));os.chdir(ff)
        from facefusion import state_manager
        from facefusion.program import create_program
        from facefusion.args import apply_args
        from facefusion.face_creator import get_static_faces
        from facefusion.face_selector import sort_faces_by_order
        apply_args(vars(create_program().parse_args(['headless-run','--execution-providers','cuda','--processors','lip_syncer','--lip-syncer-model',s['mouth_model']])),state_manager.init_item)
    width,height=media['width'],media['height'];output=run/'mouth-only.mp4';metrics=[]
    if not jobs:shutil.copyfile(run/'original-picture.mp4',output)
    else:
        cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{width}x{height}','-r',str(fps),'-i','pipe:0','-i',run/'original-picture.mp4','-map','0:v:0','-map','1:a:0','-c:v','libx264','-crf',str(s['crf']),'-preset',s['preset'],'-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',output]
        with (run/'composite-ffmpeg.log').open('w') as log:
            proc=subprocess.Popen([str(x) for x in cmd],stdin=subprocess.PIPE,stderr=log)
            cap=cv2.VideoCapture(str(run/'source.mkv'));readers={j['proposal']:cv2.VideoCapture(j['proposal']) for j in jobs}
            try:
                for frame in range(total):
                    ok,src=cap.read()
                    if not ok:raise ValueError(f'Original ended at frame {frame}')
                    result=src;j=next((j for j in jobs if j['a']<=frame<j['b']),None)
                    if j:
                        ok,proposal=readers[j['proposal']].read()
                        if not ok:raise ValueError('Proposal ended early')
                        protected=any(frame/float(fps)<b and (frame+1)/float(fps)>a for a,b in c.get('protected_audio',[]))
                        faces=[] if protected else get_static_faces([src])
                        if faces:
                            mouth=sort_faces_by_order(faces,j['order'])[0].landmark_set['68'][48:68];center=(mouth.min(0)+mouth.max(0))/2
                            poly=(mouth-center)*s['mouth_expand']+center;mask=np.zeros((height,width),np.uint8);cv2.fillConvexPoly(mask,cv2.convexHull(poly.astype(np.int32)),255)
                            mask=cv2.GaussianBlur(mask,(s['mouth_blur'],s['mouth_blur']),s['mouth_sigma']).astype(float)/255
                            result=np.rint(src*(1-mask[:,:,None])+proposal*mask[:,:,None]).astype(np.uint8)
                            assert np.array_equal(src[mask==0],result[mask==0]);metrics.append(dict(frame=frame,cue=j['id'],outside_mask_changed=0))
                        else:metrics.append(dict(frame=frame,cue=j['id'],retained_original=True,reason='protected' if protected else 'no_face'))
                    proc.stdin.write(result.tobytes())
            finally:
                cap.release()
                for reader in readers.values():reader.release()
                proc.stdin.close()
                status=proc.wait()
            if status:raise RuntimeError('Compositor encode failed; see composite-ffmpeg.log')
    write(run/'lips-receipt.json',dict(jobs=jobs,metrics=metrics,missing_face_frames=sum(x.get('reason')=='no_face' for x in metrics),outside_mask_equal_before_encode=True))
    done(run,'lips',files+[output,run/'lips-receipt.json'])

def finish(run,c,p):
    s=c['settings'];media=json.loads((run/'media.json').read_text());fps=Fraction(media['fps']);duration=media['frames']/float(fps);width,height=media['width'],media['height'];out=run/'edited.mp4'
    inserts=c.get('inserts',[]);title=c.get('title');filters=[];args=['ffmpeg','-v','error','-y','-i',run/'mouth-only.mp4'];current='0:v:0';index=1
    for i,x in enumerate(inserts):
        args += ['-i',x['image']];frames=max(1,round((x['end']-x['start'])*float(fps)));z0=x.get('zoom_start',1.015);z1=x.get('zoom_end',1.03)
        if z0<1 or z1<1:raise ValueError('Insert zoom must be >=1')
        filters.append(f"[{index}:v]scale={width}:{height},setsar=1,zoompan=z='{z0}+({z1}-{z0})*on/{max(1,frames-1)}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s={width}x{height}:fps={fps},setpts=PTS+{x['start']}/TB[insert{i}]")
        a=math.ceil(x['start']*float(fps));b=math.ceil(x['end']*float(fps))-1
        filters.append(f"[{current}][insert{i}]overlay=enable='between(n,{a},{b})':eof_action=pass[v{i}]");current=f'v{i}';index+=1
    audio='0:a:0';end_frames=media['frames']
    if title:
        seconds=title.get('duration',4);frames=round(seconds*float(fps));seconds=frames/float(fps);fade=min(title.get('scene_fade',.8),duration)
        args+=['-loop','1','-framerate',str(fps),'-t',str((frames+1)/float(fps)),'-i',title['image']]
        filters.append(f'[{current}]trim=end_frame={media["frames"]},setsar=1,format=yuv420p,settb=AVTB,setpts=N/({fps}*TB),fade=t=out:st={duration-fade}:d={fade}[scene]')
        fin=min(title.get('fade_in',.65),seconds);fout=min(title.get('fade_out',.65),seconds)
        filters.append(f'[{index}:v]scale={width}:{height},trim=end_frame={frames},setsar=1,format=yuv420p,settb=AVTB,setpts=N/({fps}*TB),fade=t=in:st=0:d={fin},fade=t=out:st={seconds-fout}:d={fout}[card]')
        filters.append('[scene][card]concat=n=2:v=1:a=0[final]');current='final'
        filters.append(f'[0:a]afade=t=out:st={duration-fade}:d={fade},apad,atrim=duration={duration+seconds}[audio]');audio='audio';end_frames+=frames
    if not filters:shutil.copyfile(run/'mouth-only.mp4',out)
    else:
        args+=['-filter_complex',';'.join(filters),'-map',f'[{current}]','-map',f'[{audio}]' if title else audio,'-c:v','libx264','-crf',str(s['crf']),'-preset',s['preset'],'-pix_fmt','yuv420p']
        args+=['-c:a','aac','-b:a',s['audio_bitrate']] if title else ['-c:a','copy']
        args+=['-r',str(fps),'-frames:v',str(end_frames),'-movflags','+faststart',out];call(args,run/'finish-ffmpeg.log')
    write(run/'finish-receipt.json',dict(output=str(out),expected_frames=end_frames,inserts=inserts,title=title,original_picture_fallback='original-picture.mp4 has the same selected scene audio before intentional title fade/padding',human_review='pending'))
    done(run,'finish',[out,run/'finish-receipt.json'])

def stream_hash(path,stream,copy=False):
    args=['ffmpeg','-v','error','-i',path,'-map',stream]
    if copy:args+=['-c','copy']
    return call(args+['-f','hash','-hash','sha256','-']).strip()

def verify(run,c,p):
    import cv2
    results=[];media=json.loads((run/'media.json').read_text());finish_info=json.loads((run/'finish-receipt.json').read_text())
    for name in ['original-picture.mp4','mouth-only.mp4','edited.mp4']:
        path=run/name;call(['ffmpeg','-v','error','-i',path,'-f','null','-']);meta=probe(path)
        cap=cv2.VideoCapture(str(path));frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));cap.release()
        expected=finish_info['expected_frames'] if name=='edited.mp4' else media['frames']
        if frames!=expected:raise ValueError(f'{name}: frame count {frames} != {expected}')
        results.append(dict(path=str(path),frames=frames,duration=meta['format']['duration'],decode='passed',sha256=sha(path)))
    if stream_hash(run/'original-picture.mp4','0:a:0')!=stream_hash(run/'mouth-only.mp4','0:a:0'):raise ValueError('A/B audio differs')
    if stream_hash(run/'source.mkv','0:v:0',True)!=stream_hash(run/'original-picture.mp4','0:v:0',True):raise ValueError('Fallback video stream changed')
    if not c.get('title') and stream_hash(run/'edited.mp4','0:a:0')!=stream_hash(run/'original-picture.mp4','0:a:0'):raise ValueError('Final scene audio changed unexpectedly')
    write(run/'verification.json',dict(files=results,comparison_audio_identical=True,fallback_video_stream_unchanged=True,title_audio_change_intentional=bool(c.get('title')),human_review='Voice, delivery, room continuity, face selection and synchronization still require playback'))
    done(run,'verify',[run/'verification.json'])

def main():
    stage=sys.argv[1];run=Path(sys.argv[2]).resolve();c=json.loads((run/'manifest.resolved.json').read_text());p=json.loads((run/'plan.json').read_text())
    os.environ['HF_HOME']=str(ROOT/'models/huggingface');os.environ['HF_HUB_OFFLINE']='1'
    if stage=='separate':separate(run,c)
    else:globals()[stage](run,c,p)

if __name__=='__main__':main()
