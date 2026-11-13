# Dialogue editing from a remembered scene

Draft for the smart-tool layer. Marc has agreed to focus the first tool on dialogue replacement and mouth-only lip sync, with Outtake providing scene discovery. The experience and connection details below are proposals, not claims of delivered behavior.

A person describes a moment in a film or show and what they want the characters to say. They get a short edited scene that retains the actors' recognizable performances, original faces and surrounding sound. They can refine a particular line or moment in ordinary language without reconstructing a technical workflow.

The tool does the routine work of finding the permitted source, identifying exchanges and visible speakers, preparing candidate dialogue, preserving room sound and applying restrained mouth animation. A person should not need to supply timestamps or edit scripts when those details can be established from the available evidence. When a meaningful ambiguity remains, the tool exposes the specific uncertainty with a useful preview or focused question. It does not animate a listener merely because someone speaks off screen.

The caller owns the conversation and presentation. Outtake owns finding and extracting source moments through its public capabilities. The dialogue tool owns turning the selected moment and replacement intent into a reviewable edit, including its connections to the rendering pipeline and configured model services. Local setup is reusable machine configuration, separate from a scene request. Amplifier provides agent reasoning and tool use; a reasoning provider does not need to be the image or speech generation backend.

An edited scene stays identifiable through discovery, generation, rendering, review and revision. The person can compare new audio over original picture with the mouth-edited version, receive an accessible file, and say what to change. Earlier useful versions survive. Work can resume after interruption without silently starting over or attaching new instructions to the wrong revision.

Human attention should go to the joke, delivery, likeness and consequential ambiguity. Routine preparation, bounded retries, file checks and recovery belong to the tool. Honest limits matter: a technically valid video is not proof of convincing speech, and uncertain speaker assignment is not a correct lip edit.

The first scope retains original faces and uses local speech editing, audio assembly and mouth-only rendering. Face swap is outside this version. Prepared artwork may be used for inserts and titles; automatic image editing is an optional capability, not a requirement for dialogue work. Neither local hardware dependencies nor missing services should be hidden behind an apparent promise of a self-contained application.

The governing draft promises are in [scene-editing](../contracts/scene-editing.md), [runtime capabilities](../contracts/runtime-capabilities.md) and [execution and delivery](../contracts/execution-and-delivery.md). Package layout, exact transport and a product name remain open.
