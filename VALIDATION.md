# Pipeline validation

Checked on Ducasse on 2026-11-12, using the existing RTX 4080 environments. No dependencies or Spark services changed. These are implementation/technical checks; new generated voice quality still needs listening review.

- Eleven unit/regression tests pass. They cover protected intervals, overlapping audio, explicit off-screen handling, speaker-label consistency, lip bounds, seed selection, dialogue markup/escaping, misspelled cue settings and cache invalidation for changed inputs/settings/corrupt outputs.
- The documented PowerShell entry point successfully runs the full fresh-generation example. Default automatic substitution markup creates the question, Whisper recognizes the target, natural-speed timing fits the slot, all unaffected PCM samples and five non-dialogue channels are unchanged, and protected audio intervals are unchanged. Twenty-seven mouth frames pass the outside-mask equality assertion with zero missing-face frames. The final title join retains the expected frame count.
- The supplied-take example also runs end to end through the PowerShell entry point. It performs new original foreground separation, accepts an existing WAV without loading the dots model, explicitly disables lips, and applies an image insert. Its final audio matches the original-picture comparison.
- A second identical invocation reused all seven stage caches. A disposable verification report was then changed. The pipeline detected its hash mismatch and reran only verification, leaving the six valid upstream stages cached.
- All three deliverables in both examples pass full FFmpeg decoding. original-picture and mouth-only contain identical decoded audio. The fallback retains the prepared source video stream. The title example intentionally fades/pads final audio.
- Sampled output frames were visually inspected for the generated question and title. This does not replace moving playback or listening.

| Example | Run directory under C:\robotdad\media\projects\pipeline-smoke\runs | Frames, original / mouth / edited |
| --- | --- | --- |
| Fresh model generation + visible lips + title | restaurant-smoke-7d4413723d9ab373 | 53 / 53 / 101 |
| Supplied WAV + separation + off-screen/no lips + insert | supplied-take-smoke-0731e331a87a3cb9 | 53 / 53 / 53 |

Each run contains its own verification.json, mix-receipt.json, lips-receipt.json, resolved manifest, identity inventory and stage logs. A previous test caught a one-frame loss at the title join; explicit frame-based timestamping fixed it, and the final test above passed.

The two examples exercise the installed six-channel source. Mono/stereo handling, different actors/languages, profiles/occlusions, long scenes and other models are implemented/configurable where documented but have not received this example's end-to-end or perceptual validation. Overlapping speakers are intentionally rejected. Timings, transcripts, protected intervals and visible-speaker selection remain editorial inputs. Concurrent writers to one run directory are unsupported.

## Canonical Retake checkout

After moving the source to amplifier-smart-tool-retake, all eleven regression tests passed again. Run-Retake.ps1 validated the original smoke manifest, and the old scene-pipeline/Run-Scene.ps1 forwarding launcher successfully planned the supplied-take example. The canonical Run-Retake.ps1 then ran the supplied-take/separation/no-lips/insert example through verify in projects/pipeline-smoke/runs/supplied-take-smoke-978255bf28a9353f. Historical run directories and receipts above remain unchanged. No earlier creative deliverable or runtime/model directory was moved.
