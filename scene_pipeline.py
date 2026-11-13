"""Manifest-driven local scene editing. Orchestrator uses only the standard library."""
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
STAGES = ['prepare', 'generate', 'check', 'mix', 'lips', 'finish', 'verify']
ENVIRONMENTS = {'prepare': 'chatterbox', 'generate': 'dots-tts', 'check': 'seed-vc',
                'mix': 'chatterbox', 'lips': 'facefusion', 'finish': 'facefusion', 'verify': 'facefusion', 'separate': 'audio-separation'}
DEFAULTS = {
    'sample_rate': 48000, 'dialogue_channels': 'auto',
    'model': 'models/huggingface/hub/models--dots-studio--dots.tts.edit/snapshots/bef1e97b4d942c62843b92c30a68961d1902b6ec',
    'precision': 'bfloat16', 'max_generate_length': 150, 'max_sequence_length': 1024,
    'speaker_scale': 1.5, 'seeds': [42, 43], 'conditioning': 'foreground',
    'separator_model': 'UVR-MDX-NET-Inst_HQ_3.onnx', 'check_words': True, 'asr_model':'openai/whisper-base.en',
    'max_tempo': 1.10, 'trim_db': 30, 'fade_ms': 15, 'handle_ms': 25,
    'mouth_model': 'wav2lip_gan_96', 'mouth_weight': 0.5,
    'mouth_expand': [1.22, 1.35], 'mouth_blur': 11, 'mouth_sigma': 2,
    'crf': 17, 'preset': 'fast', 'audio_bitrate': '512k'
}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4*1024*1024), b''): h.update(block)
    return h.hexdigest()

def write(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(obj, indent=2), encoding='utf-8'); temp.replace(path)

def call(args, log=None):
    if log:
        with Path(log).open('w', encoding='utf-8') as f:
            result = subprocess.run([str(x) for x in args], stdout=f, stderr=subprocess.STDOUT)
        if result.returncode: raise RuntimeError(f'Command failed; see {log}')
    else:
        result = subprocess.run([str(x) for x in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode: raise RuntimeError(result.stderr[-5000:])
        return result.stdout

def probe(path):
    return json.loads(call(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]))

def resolve(base, value):
    p = Path(value); return str((p if p.is_absolute() else base/p).resolve())

def interval(value, label):
    if len(value) != 2 or not all(isinstance(x, (float, int)) and math.isfinite(x) for x in value):
        raise ValueError(f'{label}: expected two finite numbers')
    if value[0] < 0 or value[1] <= value[0]: raise ValueError(f'{label}: invalid interval {value}')
    return value

def overlaps(a, b): return max(a[0], b[0]) < min(a[1], b[1])

def validate(c):
    if c.get('version') != 1: raise ValueError('version must be 1')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', c.get('name', '')): raise ValueError('name must be a simple identifier')
    if not isinstance(c.get('source'), dict) or not c['source'].get('path'): raise ValueError('source.path is required')
    if set(c['source'])-{'path','start','end','foreground'}:raise ValueError('Unknown source setting')
    start = c['source'].get('start', 0); end = c['source'].get('end')
    if not isinstance(start,(float,int)) or not math.isfinite(start) or start < 0 or (end is not None and (not isinstance(end,(float,int)) or not math.isfinite(end) or end <= start)): raise ValueError('Invalid source trim')
    cues = c.get('cues', [])
    if not cues: raise ValueError('Add at least one cue with source_text, target_text, start and end')
    protected = [interval(x, 'protected_audio') for x in c.get('protected_audio', [])]
    ids = set(); spans = []
    for q in cues:
        if set(q)-{'id','speaker','start','end','source_text','target_text','lips','take','conditioning','seeds','selected_seed','instruction','tempo_limit','gain','onset_shift_seconds'}:raise ValueError(f'Unknown cue setting in {q.get("id")}')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', str(q.get('id', ''))): raise ValueError('Invalid cue id')
        if q['id'] in ids: raise ValueError(f'Duplicate cue {q["id"]}')
        ids.add(q['id']); span = interval([q['start'], q['end']], q['id'])
        if any(overlaps(span, x) for x in spans): raise ValueError('Overlapping audio cues are not supported; split/resolve overlapping speakers explicitly')
        spans.append(span)
        if any(overlaps(span, x) for x in protected): raise ValueError(f'Cue {q["id"]} intersects protected audio; split it around the protected interval')
        if not q.get('speaker') or not q.get('source_text') or not q.get('target_text'): raise ValueError(f'Cue {q["id"]} needs speaker, source_text and target_text')
        if 'lips' not in q: raise ValueError(f'Cue {q["id"]}: explicitly set lips=[] for off-screen speech or supply visible-speaker intervals')
        lip_spans = []
        for lip in q['lips']:
            s = interval([lip['start'], lip['end']], 'lips')
            if s[0] < span[0] or s[1] > span[1]: raise ValueError('Lip interval must lie inside its audio cue')
            if not lip.get('face_order') or not lip.get('speaker') == q['speaker']: raise ValueError('Each lip interval needs matching speaker and face_order')
            if lip['face_order'] not in ['left-right','right-left','top-bottom','bottom-top','small-large','large-small','best-worst','worst-best']: raise ValueError('Unsupported face_order')
            if any(overlaps(s, x) for x in lip_spans): raise ValueError('Overlapping lip intervals')
            lip_spans.append(s)
        if 'take' in q and not q['take'].get('path'): raise ValueError('take.path required')
        if q.get('tempo_limit', c['settings']['max_tempo']) < 1: raise ValueError('tempo_limit must be >=1')
        if not q.get('take'):
            seeds=q.get('seeds', c['settings']['seeds'])
            if not seeds or any(type(x) is not int for x in seeds) or len(set(seeds))!=len(seeds): raise ValueError('seeds must be unique integers')
            if q.get('selected_seed',seeds[0]) not in seeds: raise ValueError('selected_seed must be in seeds')
    if c['settings']['sample_rate'] != 48000: raise ValueError('This version uses 48000 Hz masters')
    if c['settings']['mouth_blur'] < 1 or c['settings']['mouth_blur'] % 2 != 1: raise ValueError('mouth_blur must be odd and positive')
    for x in c.get('inserts', []): interval([x['start'], x['end']], 'insert')
    inserts=c.get('inserts', [])
    for i,x in enumerate(inserts):
        if any(overlaps([x['start'],x['end']],[y['start'],y['end']]) for y in inserts[:i]): raise ValueError('Overlapping inserts are not supported')
    t=c.get('title')
    if t and (not t.get('image') or t.get('duration',4)<=0): raise ValueError('title needs image and positive duration')
    if t and any(t.get(k,default)<=0 for k,default in [('scene_fade',.8),('fade_in',.65),('fade_out',.65)]): raise ValueError('Title fades must be positive')
    if c['settings']['conditioning'] not in ['foreground','original']: raise ValueError('Invalid conditioning')
    if c['settings']['fade_ms']<0 or c['settings']['handle_ms']<0: raise ValueError('Negative mix fade/handle')

def load_manifest(path):
    path=Path(path).resolve(); c=json.loads(path.read_text(encoding='utf-8-sig'))
    unknown=set(c)-{'version','name','source','output_dir','settings','cues','protected_audio','inserts','title','tools'}
    if unknown: raise ValueError(f'Unknown top-level keys {sorted(unknown)}')
    unknown=set(c.get('settings',{}))-set(DEFAULTS)
    if unknown: raise ValueError(f'Unknown settings {sorted(unknown)}')
    c['settings']={**DEFAULTS,**c.get('settings',{})}; validate(c)
    if set(c.get('tools',{}))-set(ENVIRONMENTS):raise ValueError('Unknown tool stage name')
    c['source']['path']=resolve(path.parent,c['source']['path'])
    if c['source'].get('foreground'): c['source']['foreground']=resolve(path.parent,c['source']['foreground'])
    for q in c['cues']:
        if q.get('take'): q['take']['path']=resolve(path.parent,q['take']['path'])
    for x in c.get('inserts',[]): x['image']=resolve(path.parent,x['image'])
    if c.get('title'): c['title']['image']=resolve(path.parent,c['title']['image'])
    c['settings']['model']=resolve(ROOT,c['settings']['model'])
    c['output_dir']=resolve(path.parent,c.get('output_dir','runs'))
    c['tools']={stage:resolve(ROOT,c.get('tools',{}).get(stage,f'{env}/.venv/Scripts/python.exe')) for stage,env in ENVIRONMENTS.items()}
    return c

def identity(c):
    paths=[c['source']['path']]
    if c['source'].get('foreground'): paths.append(c['source']['foreground'])
    paths += [q['take']['path'] for q in c['cues'] if q.get('take')]
    paths += [x['image'] for x in c.get('inserts',[])]
    if c.get('title'): paths.append(c['title']['image'])
    inputs={str(p):sha(p) for p in sorted(set(paths))}
    tools={str(p):sha(p) for p in HERE.glob('*.py') if not p.name.startswith('test_')}
    for env in set(ENVIRONMENTS.values()):
        p=ROOT/env/'requirements.lock.txt'
        if p.exists(): tools[str(p)]=sha(p)
    for p in [ROOT/'facefusion/local_run.py',ROOT/'dots-tts/src/dots_tts/edit_runtime.py']:
        if p.exists(): tools[str(p)]=sha(p)
    # Include local library patches, plus model inventory changes. Snapshot
    # revisions identify weights; size/mtime catches local replacement without
    # rehashing gigabytes for every plan/resume operation.
    for folder in [ROOT/'facefusion/facefusion',ROOT/'dots-tts/src/dots_tts']:
        for p in folder.rglob('*.py'):tools[str(p)]=sha(p)
    models={}
    folders=[Path(c['settings']['model']),ROOT/'facefusion/.assets/models',ROOT/'models/separation']
    for folder in folders:
        if folder.is_dir():
            for p in sorted(folder.rglob('*')):
                if p.is_file() and p.suffix in ['.json','.safetensors','.onnx','.hash','.pt','.bin']:
                    stat=p.stat();models[str(p)]={'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}
                    if p.suffix in ['.json','.hash']:models[str(p)]['sha256']=sha(p)
    ffmpeg=call(['ffmpeg','-version']).splitlines()[0]
    obj={'config':c,'inputs':inputs,'tools':tools,'models':models,'ffmpeg':ffmpeg}
    key=hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()
    return key,obj

def build_plan(c):
    meta=probe(c['source']['path']); video=next(s for s in meta['streams'] if s['codec_type']=='video'); audio=next(s for s in meta['streams'] if s['codec_type']=='audio')
    fps=Fraction(video['r_frame_rate']); avg=Fraction(video['avg_frame_rate'])
    if video['width']%2 or video['height']%2:raise ValueError('Normalize odd video dimensions before H.264 rendering')
    if fps<=0 or abs(float(fps-avg))>.001: raise ValueError('Variable-frame-rate source: normalize explicitly before using this pipeline')
    duration=float(meta['format']['duration']); start=c['source'].get('start',0); end=c['source'].get('end',duration)
    if start>=duration or end>duration+.05: raise ValueError('Source trim exceeds media duration')
    local=end-start
    for q in c['cues']:
        if q['end']>local: raise ValueError(f'Cue {q["id"]} exceeds source trim')
    for x in c.get('protected_audio',[]):
        if x[1]>local: raise ValueError('Protected interval exceeds clip')
    for x in c.get('inserts',[]):
        if x['end']>local: raise ValueError('Insert exceeds clip')
    channels=c['settings']['dialogue_channels']; count=int(audio['channels']); layout=audio.get('channel_layout','')
    if channels=='auto':
        if layout in ['5.1','5.1(side)','7.1','7.1(wide)','3.0','4.0']: channels=[2]
        elif count==1: channels=[0]
        elif count==2: channels=[0,1]
        else: raise ValueError(f'Unknown channel layout {layout!r}; set dialogue_channels explicitly')
    if not isinstance(channels,list) or not channels or any(type(i)is not int or i<0 or i>=count for i in channels) or len(set(channels))!=len(channels): raise ValueError('Invalid dialogue_channels')
    return {'fps':str(fps),'width':video['width'],'height':video['height'],'channels':count,'layout':layout,'dialogue_channels':channels,'source_start':start,'duration':local,'source_probe':meta}

def stage_valid(run, stage):
    receipt=run/f'{stage}.done.json'
    if not receipt.exists(): return False
    try:
        outputs=json.loads(receipt.read_text())['outputs']
        return bool(outputs) and all((run/p).is_file() and sha(run/p)==h for p,h in outputs.items())
    except (ValueError,KeyError,OSError): return False

def template():
    return {'version':1,'name':'new-scene','source':{'path':'source.mp4'},'output_dir':'runs','settings':{},'protected_audio':[],
            'cues':[{'id':'line-01','speaker':'speaker-a','start':1.0,'end':3.0,'source_text':'Original dialogue.','target_text':'Replacement dialogue.','seeds':[42,43],'selected_seed':42,'lips':[]}], 'inserts':[]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    init=sub.add_parser('init');init.add_argument('manifest')
    for name in ['validate','plan','run']:
        p=sub.add_parser(name);p.add_argument('manifest')
        if name=='run':p.add_argument('--through',choices=STAGES,default='verify');p.add_argument('--force',action='store_true')
    args=parser.parse_args()
    if args.command=='init':
        path=Path(args.manifest)
        if path.exists(): raise ValueError('Refusing to overwrite existing manifest')
        write(path,template());print(path.resolve());return
    c=load_manifest(args.manifest);plan=build_plan(c)
    for executable in c['tools'].values():
        if not Path(executable).is_file():raise ValueError(f'Runtime missing: {executable}')
    if not Path(c['settings']['model']).is_dir() and any(not q.get('take') for q in c['cues']):raise ValueError('Speech model path missing')
    if args.command=='validate': print(json.dumps({'valid':True,'scene':c['name'],'plan':{k:v for k,v in plan.items() if k!='source_probe'}},indent=2));return
    key,record=identity(c);run=Path(c['output_dir'])/f'{c["name"]}-{key[:16]}'
    if args.command=='plan':print(json.dumps({'run_dir':str(run),'stages':STAGES,'identity':key,'plan':{k:v for k,v in plan.items() if k!='source_probe'}},indent=2));return
    run.mkdir(parents=True,exist_ok=True);write(run/'manifest.resolved.json',c);write(run/'identity.json',record);write(run/'plan.json',plan)
    dirty=args.force
    for stage in STAGES[:STAGES.index(args.through)+1]:
        if not dirty and stage_valid(run,stage): print(f'{stage}: cached',flush=True);continue
        dirty=True
        for downstream in STAGES[STAGES.index(stage):]: (run/f'{downstream}.done.json').unlink(missing_ok=True)
        print(f'{stage}: running -> {run}',flush=True)
        call([c['tools'][stage],HERE/'worker.py',stage,run],run/f'{stage}.log')
        if not stage_valid(run,stage): raise RuntimeError(f'{stage} did not produce a valid output receipt')
    print(json.dumps({'run_dir':str(run),'completed_through':args.through,'human_review':'Required for voice, room mix, visible-speaker assignment and lip quality'},indent=2))

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,StopIteration,KeyError,TypeError) as e:print(f'ERROR: {e}',file=sys.stderr);sys.exit(1)
