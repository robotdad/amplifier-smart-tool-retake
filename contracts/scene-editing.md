# Scene editing and caller interaction

Draft behavioral proposal for Retake (amplifier-smart-tool-retake). The product name and voice/mouth-only first scope are agreed; detailed connection promises below remain proposals. For the calling agent, Retake, Outtake and the person reviewing the result. Marc owns product direction. The local implementation owns integration within the agreed scope; it does not change Outtake's promises or Spark configuration unilaterally.

## Promises

1. A request can contain a title/source hint, a description of the moment, replacement dialogue and relevant constraints. It need not contain timestamps, a transcript or a render manifest. The tool obtains missing technical preparation through configured capabilities. It does not falsely report successful preparation when those capabilities are absent.
2. Discovery and source extraction use Outtake's public library capabilities and retained identifiers/results, not parsed CLI prose or private agent transcripts. Source roots and output scope come from caller-owned configuration. A proposed source is distinguished from an evidenced match. Ambiguous occurrences remain distinguishable; subsequent refinements retain the selected source/occurrence.
3. Before rendering, the tool has explicit source-relative timing, exact intended dialogue, speaker assignments, separate visible-speaker intervals and protected reactions/room-audio intervals. Internal automation may produce these records. The caller does not have to author them manually. Material uncertainty is returned as evidence and a specific unresolved choice, not silently converted into a confident assignment.
4. Each changed exchange uses its own original performance where source-performance editing is requested. The tool does not recycle one generated token across distinct original deliveries. Off-screen speech has no lip edit on visible listeners. Overlap that the current processing cannot handle is reported before destructive replacement.
5. The mix uses the original soundtrack as its base and limits foreground replacement to selected speech windows/channels. Laughter, breaths and reactions outside those windows remain protected. Separation inside overlapping foreground is approximate and cannot be advertised as exact recovery of hidden background. No artificial reverb is added by default.
6. With original faces retained, lip generation supplies a proposal. Only a tracked, feathered mouth region is composited over original picture. Failed detection retains original picture and is reported as partial coverage. Broader facial regeneration or face swap is outside this version.
7. Feedback identifies the scene, revision and affected exchange/shot. A request such as "retry the question" either resolves to a known target or returns distinguishable choices. It does not silently select a different occurrence, rewrite unrelated lines or apply a correction to a newer revision the person has not seen.
8. Prepared inserts/titles are optional finishing operations. Automatic image generation/editing is offered only when the required configured capability is available. Dialogue editing remains usable without it. This does not authorize a silent switch to a cloud image provider or a different visual technique.

## Checks

Walk a remembered-scene request through Outtake discovery, evidence, automatic preparation and both edited exports without manually writing cue JSON. Include two plausible source occurrences, an off-screen line, varied intonation, laughter between words and an unavailable preparation capability. The tool must preserve uncertainty and selected identity across each transition. Follow a targeted correction and verify that unrelated decisions stay fixed.

Listening is needed to judge identity, delivery and audible artifacts. Agent checks must still catch routine failures before asking the person to rescue them. A manifest-only runner does not meet promise 1 or 3 by itself.

## Deliberate choices and open details

Outtake is the proposed retrieval/extraction dependency and the existing pipeline is the starting rendering component. These choices reuse capabilities already exercised and preserve their independent responsibilities. Precise automatic alignment/speaker-assignment mechanisms, request schemas and transport are open until their connection can be demonstrated. An unavailable service must not be treated as an implicitly working dependency.
