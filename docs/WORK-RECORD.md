# Smart-tool work record

Updated 2026-11-12. Governing methodology is [Amplifier Converge](https://github.com/microsoft/amplifier-converge/tree/e39fe7676ba88737319bca21af78dd0f819eb8a3), inspected at e39fe7676ba88737319bca21af78dd0f819eb8a3. Read its vision, six contracts, agent/reviewer guides and writing guide. The reference checkout is C:\robotdad\media\reference\amplifier-converge. This application is a document/scenario review, not live smart-tool verification.

## Direction and authority

Marc owns product direction. The accepted first focus from this conversation is dialogue replacement and mouth-only lip sync, retaining original faces, using Outtake for scene discovery and the existing local pipeline for rendering. Face swap is deferred. Follow Converge for further work.

The draft [vision](VISION.md) and [contracts](../contracts/scene-editing.md) make proposed behavior reviewable. They do not turn prior architectural suggestions into accepted detailed commitments or authorize publishing, new paid-provider use, deployment or Spark administration. The local implementation can prepare/review these drafts and investigate existing capabilities within current authority. The other agent retains Spark ownership.

## Current reality

- The local JSON-driven pipeline is implemented and component-tested. See [validation](../VALIDATION.md) for the exact covered examples and limits.
- Outtake's installed public library owns bounded discovery, observation, plans and extraction. Its installed smart runtime uses specific reasoning providers. Its live provider-backed scene finding has not been validated in this media setup.
- The current pipeline still needs explicit transcripts, cue timing and visible-speaker intervals. It is not yet the described natural-language smart tool.
- No machine-profile/adapter boundary or automatic preparation layer has been implemented for that tool.
- Generated menu/title artwork used this chat's image generation capability. The standalone pipeline accepts prepared artwork. No local image-edit adapter or Spark workflow has been validated here.

## Contract review and next useful outcome

Prepare one narrow connected outcome: a described moment in a known title plus a bounded replacement instruction produces a retained proposed edit, with Outtake source evidence and automatic timing/speaker preparation, then the existing render comparisons. Include an off-screen exchange and protected laughter in its verification. Keep automatic image editing optional and face swap outside the first implementation.

The next implementation assignment should name its owner, execution/provider scope and limits, connection versions, completion evidence and recovery behavior. No new implementation assignment or workers were started by this methodology review.

| Boundary | Gap exposed by review | Proposed home / consequence |
| --- | --- | --- |
| Caller to dialogue tool | Natural-language intent currently stops at manually authored JSON | scene-editing contract, promises 1-3; automatic preparation is necessary for the intended experience |
| Dialogue tool to Outtake | CLI wrapping could depend on private text or lose source identity | scene-editing contract, promise 2; public library results/retained IDs |
| Tool to machine/backends | Provider support and local service labels could be mistaken for usable generation | runtime-capabilities contract; capability checks and explicit profile/adapter boundary |
| Revision to renderer | A changed line could reuse stale lips or the wrong selected take | execution-and-delivery contract, promises 1-2 and 6 |
| Checks to delivery | Component success could be presented as natural-language workflow success | execution-and-delivery contract, promises 4-7; verify the actual combined user journey |

Exact schemas, provider routing, transcription/alignment/speaker mechanisms, job recovery implementation and optional image backend remain proposed/open. The installed pipeline informs feasibility but does not settle those product connections.

## Scenario walkthrough

For "find the restaurant scene and change each spoken name," the proposed contracts allow bounded Outtake discovery, preserve candidate/occurrence identity, build per-performance edits and leave off-screen listeners alone. A laugh between words becomes a protected interval, not synthesized laughter. With no image-edit capability, the dialogue path still works and the requested menu change is reported as unavailable or uses explicitly supplied artwork. A follow-up targets a particular retained revision/exchange; it cannot silently rewrite a different cut. A dropped backend acknowledgement leads to inspecting the job before retrying.

This tabletop walkthrough supports clarity of the draft, not proof those behaviors execute. Live acceptance still needs the connected outcome above. Review found no need for routine human sign-off on cue preparation, bounded retries or ordinary implementation choices within standing authority. Consequential new scope stays distinguishable from those choices.
