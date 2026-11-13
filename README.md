# Retake

Rewrite the dialogue. Keep the performance.

Private source repository: [robotdad/amplifier-smart-tool-retake](https://github.com/robotdad/amplifier-smart-tool-retake).

Retake is the agreed product name; amplifier-smart-tool-retake is the repository. For the proposed Amplifier smart-tool layer, start with [docs/VISION.md](docs/VISION.md), the [contracts](contracts/scene-editing.md) and [current work record](docs/WORK-RECORD.md). These apply Amplifier Converge and distinguish the agreed first scope from draft connection details. The runner documented below is the existing component, not a completed natural-language agent experience.

Manifest-driven dialogue replacement with original faces and room sound. Runs on Ducasse using the existing isolated environments. No project-specific Python edits are needed for another scene.

The scene file supplies the source, source/replacement dialogue, cue timing, visible-speaker intervals, selected seeds or existing takes, protected audio, optional image inserts and an end card. The pipeline generates speech, checks words, mixes audio, applies mouth-only lip sync, finishes and verifies exports.

Machine layout, installed dependencies and the surrounding production guides are described in [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md). DGX Spark advice remains in the local workspace PRODUCTION-WORKFLOW.md under Spark agent setup request. Retake does not install or change services on the Sparks.

## Quick start

Run in PowerShell from C:\robotdad\media. Put a source clip beside the new scene JSON, or use an absolute source path.

```powershell
.\amplifier-smart-tool-retake\Run-Retake.ps1 init .\projects\next-scene\scene.json
# Edit scene.json with the source, original dialogue, replacement dialogue and times.
.\amplifier-smart-tool-retake\Run-Retake.ps1 validate .\projects\next-scene\scene.json
.\amplifier-smart-tool-retake\Run-Retake.ps1 plan .\projects\next-scene\scene.json
.\amplifier-smart-tool-retake\Run-Retake.ps1 run .\projects\next-scene\scene.json -Through mix
# Audition selected speech and the room mix before full rendering.
.\amplifier-smart-tool-retake\Run-Retake.ps1 run .\projects\next-scene\scene.json
```

The first command creates parent directories and refuses to overwrite an existing manifest. Edit JSON data only. The same CLI works directly through the existing Python runtime if PowerShell script execution is unavailable.

```powershell
& .\facefusion\.venv\Scripts\python.exe .\amplifier-smart-tool-retake\scene_pipeline.py run .\projects\next-scene\scene.json --through mix
```

`run` executes every prerequisite through the requested stage. Stages are prepare, generate, check, mix, lips, finish and verify. `-Through generate` leaves all candidate WAVs for auditioning. `-Through check` adds ASR reports. Change selected_seed or point take.path to the chosen file, then rerun. The manifest and input hashes determine a new output directory when inputs/settings change.

## Scene file

All cue, lip, protected-audio and insert times are seconds relative to the extracted clip, after source.start. Relative file paths resolve against the scene JSON directory, not the current shell directory. Use forward slashes in JSON paths or escape backslashes.

```json
{
  "version": 1,
  "name": "next-scene",
  "source": {"path": "source.mp4", "start": 10, "end": 20},
  "output_dir": "runs",
  "settings": {},
  "protected_audio": [[4.2, 4.8]],
  "cues": [
    {
      "id": "question",
      "speaker": "speaker-a",
      "start": 1.0,
      "end": 3.0,
      "source_text": "Original question?",
      "target_text": "Replacement question?",
      "seeds": [42, 43],
      "selected_seed": 42,
      "lips": [
        {"start": 1.0, "end": 2.3, "speaker": "speaker-a", "face_order": "left-right"}
      ]
    }
  ],
  "inserts": [],
  "title": {"image": "title.png", "duration": 4, "scene_fade": 0.8, "fade_in": 0.65, "fade_out": 0.65}
}
```

Omit start/end to process a complete clip. Exact source trimming re-encodes video at CRF 16 to establish accurate boundaries. Untrimmed input retains the source video stream through preparation. An original-picture export copies the prepared source stream in either case. The probe and preparation receipt record this distinction.

Original dialogue and timings must be supplied/reviewed. This version does not autonomously infer speaker identity, diarize overlapping voices, locate all scene cuts or decide what to rewrite. Those are editorial inputs. It rejects overlapping speech edits instead of guessing how to separate simultaneous speakers. Split around pauses/laughter that must remain unchanged.

For off-screen speech set `"lips": []`. This is mandatory and explicit. For visible speech, supply one lip interval per shot/visibility span. It can be shorter than the audio exchange. Face order is shot-specific, not a persistent identity tracker. A matching speaker label guards manifest consistency but cannot prove the selected person is correct. Review representative frames and playback.

For a localized substitution, optional `instruction` can use the tested dots markup while source_text and target_text still give the complete exact transcripts.

```json
"instruction": "<sub targ=\"Amplifier\">Malkovich</sub>?"
```

Without instruction, the runtime wraps the original text in a substitution targeting the replacement text, keeping shared final punctuation outside the tag. For multiple precise word edits within otherwise unchanged dialogue, provide explicit sub tags to retain that context. Quotes/markup are data, never shell commands.

## Existing takes and alternate voice tools

Instead of seeds/selected_seed, a cue can supply a selected WAV. The pipeline will not load the dots model if every cue has a supplied take.

```json
"take": {"path": "takes/chosen-line.wav", "crop": [0.15, 1.4]}
```

Crop is optional and relative to that WAV. Audio is converted to mono at 48 kHz. A word check still compares it to target_text unless explicitly disabled. Provided takes let another voice tool feed the same audio preservation, timing, lip and delivery stages. Do not put the original room mix into a replacement take.

Optional source.foreground points to an already estimated original foreground WAV aligned to the full source.path timeline. The pipeline applies source.start to it. Otherwise it estimates foreground once with the existing audio-separator runtime. This is still approximate under overlapping speech/music. It does not turn a stereo mix into clean isolated dialogue.

## Settings

Overrides go in the settings object. Unknown setting names are rejected. The defaults live in scene_pipeline.py and are saved in each resolved manifest.

| Setting | Default / behavior |
| --- | --- |
| model | Installed dots.tts.edit revision bef1e97b4d942c62843b92c30a68961d1902b6ec |
| precision / max_generate_length / max_sequence_length | bfloat16 / 150 / 1024, optimize=False |
| speaker_scale | 1.5, use_xvector=True |
| conditioning | foreground; a cue can override with original |
| seeds | [42,43], directly passed as the RNG seeds; no cue-number offset |
| check_words / asr_model | true / openai/whisper-base.en in the populated local cache |
| sample_rate | 48000, PCM_24 masters |
| dialogue_channels | auto; center index 2 for recognized center-bearing layouts, mono index 0, both channels for stereo |
| max_tempo | 1.10; refuse larger required speedup unless a cue explicitly sets tempo_limit |
| trim_db / handle_ms / fade_ms | 30 / 25 / 15 |
| separator_model | UVR-MDX-NET-Inst_HQ_3.onnx |
| mouth_model / mouth_weight | wav2lip_gan_96 / 0.5 |
| mouth_expand / mouth_blur / mouth_sigma | [1.22,1.35] / 11 / 2 |
| crf / preset / audio_bitrate | 17 / fast / 512k |

Use explicit dialogue_channels when layout is ambiguous. Stereo replacement subtracts the shared estimated foreground and adds selected speech in both channels. This is an approximation, not center-only editing or perfect stereo background preservation. Mono/stereo and explicit channel modes need their own listening review. Non-dialogue channels and samples outside the edit masks are asserted unchanged before encoding.

Cue overrides include conditioning, seeds, selected_seed, instruction, take, tempo_limit, gain and onset_shift_seconds. Default onset is detected from the original foreground. onset_shift_seconds is an explicit adjustment relative to that onset, useful only after reviewing the source timing. The default never silently advances a word to avoid a laugh. A clip/word that cannot fit raises an error instead of truncating the word. Retry before raising tempo_limit.

Timing uses the tested Rubber Band options, constant active-speech RMS gain and a feathered foreground replacement. No artificial reverb is added. Model output goes directly to the selected take path; no automatic second separation of synthesized speech is applied. Existing scene takes are not all made with that method; consult the playbook for historical differences.

ASR checks all candidates and reports matches in word-check.json. Only a selected candidate mismatch stops the pipeline. ASR can fail on valid speech. `"check_words": false` is an explicit override for reviewed takes or unsupported languages, recorded in the receipt; it disables ASR trimming as well. It does not establish creative acceptance. Another cached compatible ASR model can be set with asr_model.

## Inserts and title

Inserts consume prepared images. This CLI does not call a cloud image generator. The agent can generate artwork separately and put its path in the manifest.

```json
"inserts": [
  {"start": 5, "end": 7, "image": "menu.png", "zoom_start": 1.015, "zoom_end": 1.03}
]
```

An insert replaces that full video region with a centered still-based push, stretched to frame size. It is not tracked text replacement on a moving prop. Use matching-aspect artwork. It preserves scene timing and audio. Inserts cannot overlap. Title is an optional prepared image appended after the scene, with configurable scene/audio fade and title fades. White calligraphic text on black is artwork, not a hardcoded film title in the runner.

## Outputs, caching and recovery

Each run directory has a content-derived suffix. It includes the resolved scene file, source/asset/take hashes, pipeline/local-library code and environment-lock hashes, FFmpeg version, model revision/file inventory, stage logs and per-stage output hashes. Model inventories record weight sizes/mtimes and config/checksum hashes rather than rehashing every large weight on every invocation. An output is reused only when its stage receipt and every output hash match. Changed inputs/settings create another run directory. If an output is missing/corrupt or a stage fails, that stage and all downstream stages rerun. Proposal files are regenerated during a fresh lips stage, never accepted merely because a filename exists.

`-Force` reruns all requested stages in the same identity directory. It deliberately overwrites that run's derived outputs. For a different creative take, change the seed/selection/config instead. Concurrent writers to the same run are not supported; run one job per manifest identity.

| File | Purpose |
| --- | --- |
| original.wav / foreground.wav | Prepared original master and estimated dialogue |
| takes/ / takes.json | Every generated/provided take, source performance and selected seed |
| word-check.json | ASR content/timestamps, not voice-quality approval |
| selected/ | Raw trimmed and Rubber Band timed takes |
| soundtrack.wav | Lossless selected surround/mono/stereo scene mix |
| dialogue-driver.wav | Isolated replacement speech in scene position |
| original-picture.mp4 | Prepared original picture with selected new scene audio |
| mouth-only.mp4 | Same audio, with only explicit visible-speaker mouth edits |
| edited.mp4 | Mouth version plus optional inserts/end card |
| mix-receipt.json / lips-receipt.json | Preservation assertions, timing/gain and missing-face coverage |
| verification.json | Decode results, frame counts, comparison audio and fallback picture checks |

original-picture and mouth-only have identical decoded scene audio. edited has the same audio too unless a title requests the intentional end fade/silence padding. The fallback excludes inserts and title, so it stays an original-picture comparison. All three files retain their own hashes in verification.json.

Inspect the stage log named by any failure. Full face changes are never a recovery action. A missing detection retains the original frame and is counted in lips-receipt.json. File hashes do not establish speaker likeness, natural intonation, preserved background beneath speech or temporal mouth quality. Listen and watch before sharing.

Models must already exist locally. HF_HUB_OFFLINE=1 is set in workers. Missing cached weights/models fail visibly. Runtime executable overrides are available in tools using stage names including separate. Paths resolve against C:\robotdad\media for those machine settings. Input video needs constant frame rate and even dimensions for the tested H.264 path. Variable frame rate must be normalized explicitly first.

## Tests and example

```powershell
& .\facefusion\.venv\Scripts\python.exe -m unittest discover -s amplifier-smart-tool-retake -v
.\amplifier-smart-tool-retake\Run-Retake.ps1 run .\amplifier-smart-tool-retake\examples\smoke.scene.json
```

The smoke scene extracts a short existing original shot, generates a fresh question, protects two room-audio intervals, renders a visible-speaker mouth pass and appends the existing title image. It writes only under projects/pipeline-smoke/runs and leaves all Being Amplifier outputs intact. The populated foreground stem is supplied to avoid repeating full-scene separation in this example.

Both the fresh-generation example and examples/supplied-take.scene.json passed end to end through the PowerShell entry point. Eleven regression tests passed. The latter example exercises automatic foreground separation, an existing WAV, explicit no-lip handling and an image insert. Cache reuse and hash-mismatch recovery were also tested. Exact outputs and remaining coverage limits are in [VALIDATION.md](VALIDATION.md).
