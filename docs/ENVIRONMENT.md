# Retake and its local environment

Retake source is separate from the installed model runtimes, media library and generated projects. A clone of this repository alone does not provision a working GPU environment. The current runner targets the existing Ducasse installation; a portable environment-profile boundary is proposed in the runtime-capabilities contract, not yet implemented.

## Ducasse layout

Canonical source is C:\robotdad\media\amplifier-smart-tool-retake. The current code derives its media root from the checkout's parent. Examples resolve input paths against their scene JSON location. Keep this checkout beside the runtime directories or explicitly configure supported runtime/model path overrides; moving it elsewhere is not automatically portable.

| Sibling directory | Purpose |
| --- | --- |
| dots-tts | Source-performance speech editing; isolated Python/CUDA environment |
| audio-separation | Original foreground estimates with audio-separator |
| seed-vc | Separate voice-conversion installation; its environment also runs cached Whisper word checks |
| facefusion | Mouth proposals, face landmarks and composition; Run-Retake.ps1 uses its Python for orchestration |
| chatterbox | Separate speech lab; pipeline uses its numeric/audio Python packages and CUDA DLL directory, without invoking Chatterbox synthesis |
| qwen3-tts | Separate direct-cloning experiments, outside the current Retake scene branch |
| models | Shared cached weights; not part of the source repository |
| outtake | Installed source/library for permitted media discovery and extraction; not yet integrated into the Retake agent layer |
| projects | Source exports, manifests, takes, receipts, renders and retained experiments |
| reference | Read-only methodology/reference checkouts |

FaceFusion's local_run.py depends on CUDA/cuDNN DLLs under the sibling Chatterbox environment. Python virtual environments also contain installation paths. Do not reorganize these directories by moving them without a migration and verification plan.

## Authoritative local guides

These belong to the surrounding workspace, not duplicated inside the product repository.

- C:\robotdad\media\README.md maps the workspace and current work.
- C:\robotdad\media\LOCAL-SETUP.md records installed versions, compatibility patches, launch/stop and recovery details.
- C:\robotdad\media\SCENE-EDITING-PLAYBOOK.md records production decisions and exact historical Being Amplifier settings.
- C:\robotdad\media\PRODUCTION-WORKFLOW.md covers overall production roles and the DGX Spark setup handoff under Spark agent setup request.
- C:\robotdad\infra\notes\machine-media-recasting.md is the durable machine/change trail.

docs/VISION.md and contracts/ govern proposed Retake product behavior. docs/WORK-RECORD.md identifies current reality and next work. VALIDATION.md records component evidence and the historical integration examples. Those checks do not establish the unimplemented agent-facing experience or remote-worker readiness.

## Runtime behavior

No package installation, service startup, model download or remote dispatch occurs merely by cloning Retake. Current workers use installed runtimes and local populated model caches. They set HF_HUB_OFFLINE=1. Per-stage tools overrides and the speech model setting exist; full environment profiles are future work.

Run-Retake.ps1 is the canonical local launcher. Run-Scene.ps1 remains a legacy name in the source, and the former C:\robotdad\media\scene-pipeline path contains forwarding launchers only. Historical receipts keep their original paths. Moving the source changes cache identity; a fresh named run is expected, not a reason to rewrite old receipts.
