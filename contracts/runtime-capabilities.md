# Local environment, agent and backend capabilities

Draft proposal. For the dialogue tool, environment administrator, Amplifier agent integration and generation/render adapters. The Windows implementation owns Ducasse integration. The existing Spark agent owns Spark provisioning; describing a remote worker is not authority to change that host.

## Promises

1. Machine-specific paths, interpreter/model versions, service endpoints, storage mappings and available workers live in a caller-owned environment profile, separate from creative requests. Credentials are referenced through the selected provider's supported credential mechanism, not embedded in a scene or artifact receipt. Model-generated plans cannot grant themselves new roots, endpoints or disclosure authority.
2. The reasoning/vision provider and generation backends are separate capabilities. An Amplifier agent may call a local speech or image-editing adapter even when its reasoning provider cannot synthesize that medium. Choosing a provider alone does not establish access to all generation capabilities.
3. Each adapter declares what operation it supports, required inputs, bounded execution conditions, output/receipt shape and relevant failures. Capabilities distinguish speech editing, transcription/alignment, frame inspection, mouth sync, text-to-image, reference-image editing and video composition. A text-to-image service is not advertised as a reference-image editor.
4. Preflight checks the actual required capabilities and usable input/output paths for the requested operation. A configured label, reachable web UI or successful import is insufficient. Validation uses an appropriate small operational check or retained evidence tied to the same configuration/version. Missing optional image services do not disable the ready dialogue path.
5. Backend dispatch uses configured paths/endpoints and stable job/artifact references. Remote execution accounts for path mapping, input transfer and result retrieval. It does not assume a Ducasse path exists on a Spark, that GPU memory combines across hosts or that an SSH connection proves a model workflow is ready.
6. Requests carry the applicable execution/disclosure scope and bounded work limits through each adapter. Routing does not silently enlarge that scope, switch local work to cloud processing or exceed retries/budget. Reversible choices within standing authority proceed without repeated approval.
7. Menu-like image edits preserve the input reference, requested exact text, selected workflow/model revision and result receipt. The selected technique is explicit: a still-based insert and tracked original prop replacement are different capabilities/results. Text and appearance are checked before the asset is used. Failed text generation remains a failed candidate, not an accepted title/menu.
8. Capability errors identify the affected operation and a useful remedy. They distinguish unavailable service, unsupported operation, incompatible model/workflow, inaccessible input/output and failed execution. Secrets and unnecessary source material are excluded from diagnostics.

## Checks

Run the same dialogue request with a valid profile, a missing speech runtime and a missing optional image backend. Test a local reasoning provider paired with a separately configured image editor, and a reasoning provider without image synthesis support. Attempt a remote job with an invalid path mapping. None should be misreported as a completed render or cause an undeclared fallback. Any provider/capability not exercised remains unverified.

## Deliberate choices and open details

The profile/adapter separation is proposed so machine administration can change without rewriting scene intent. Local installed runtimes are the first target. ComfyUI is a candidate image backend, not a verified current dependency. Exact adapter protocol, profile schema, worker scheduling and specific image workflow/model remain open. The tool does not require installing a new service simply to draft or review this contract.
