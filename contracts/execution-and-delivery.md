# Execution, revision, verification and delivery

Draft proposal. For the tool's job owner, render pipeline, caller and reviewer. The dialogue tool remains accountable for the combined result until a usable output or an honest unresolved outcome is returned. Dispatching a backend job does not establish completion.

## Promises

1. A durable work record identifies the scene request, source/occurrence, creative revision, execution/job identity, selected takes, dependencies, capability profile, limits, observed results and next useful action. The request, a creative revision and a processing attempt are distinguishable. A caller can reopen or inspect work without starting a new render.
2. Input/configuration changes invalidate affected cached work. A proposal is not reused solely because a filename exists. After uncertain acknowledgement or interruption, the tool inspects the identified job and existing effects before resubmitting, preventing duplicated paid/GPU work within the declared retry scope.
3. Backend jobs have bounded retries and report partial progress/failure honestly. Cancellation acknowledgement is distinguished from an actually stopped worker. Another executor must not take over while an earlier worker can still publish conflicting results. Parallel work must respect shared GPU/service constraints.
4. Each proposed output is checked across the integrated path that produced it. Word checks do not prove voice identity; decoding does not prove sync; frame-level masks do not prove correct speaker choice. Evidence records the actual version, conditions, observation and limits, with checks capable of exposing likely failures.
5. The tool verifies edited words, complete word boundaries, duration/timing fit, clipping, relevant audio preservation, correct visible-speaker assignment, bounded mouth changes, missing-face coverage, frame count/FPS/layout and decoding. Speech quality and temporal lip behavior receive appropriate playback evaluation; any unavailable perceptual check stays unverified rather than being silently replaced by ASR.
6. Original-picture/new-audio and mouth-only comparisons derive from the same selected scene soundtrack. An intentional ending fade/title/padding is reported separately. Earlier useful revisions remain available. Receipts identify the artifacts that actually carry the correction.
7. Delivery includes a usable output location and comparison material the caller can present. A local filesystem path is not claimed to be phone-accessible. If phone delivery is requested, the actual configured download/playback route is exercised or its missing verification is disclosed. A promised future notification or unattended continuation needs a working mechanism.
8. Natural feedback is traced to the observed artifact/revision, investigated, and converted into a correction, an explicit product decision or a concrete remaining limitation. Repeated failures reopen verification. Useful lessons strengthen the relevant contract, implementation or check so the person need not repeat the same diagnosis.

## Checks

Exercise request -> Outtake selection -> automatic preparation -> speech -> original-picture comparison -> mouth-only output -> accessible delivery. Inject a wrong source occurrence, wrong visible speaker, distorted selected take, stale lip proposal, lost job acknowledgement, unavailable service and interrupted render. The integrated check should expose the relevant fault, retain useful work and resume/revise the identified job without unrelated edits or duplicate execution.

This walkthrough is acceptance evidence to obtain, not a claim it has already passed. Technical pipeline tests remain component evidence. Human creative acceptance is separate from those tests and does not relieve the tool of routine verification.

## Open details

Job storage, concurrency mechanism, cancellation protocol, perceptual check mechanisms and caller notification transport remain open. The first connected implementation should establish one bounded request/revision path before expanding backend or worker choices.
