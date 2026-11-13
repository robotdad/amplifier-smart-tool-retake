# Retake motion identity

Concept: keep the frame, replace the line. A geometric R contains a speech-balloon counter and a contrasting replacement stroke. The wordmark holds still while Old line is crossed out and New line appears. TAKE 01 changes to TAKE 02. The loop returns to the initial state over six seconds without a hard cut.

Authored as native HTML/SVG plus a seekable GSAP timeline. Rendered directly in HyperFrames 0.8.33, using GSAP 3.14.2 and the isolated pinned Node runtime. Unfold's documented HyperFrames backend informed the approach, but no Unfold agent session was used. The rejected generated clapperboard candidate was excluded.

Outputs are committed in ../assets so a website build needs no renderer. retake-loop.mp4 is the local silent 1200x720/30fps master, retake-loop.gif is the six-second 1000x600/15fps web loop, retake-static.png is the 1200x720 completed state at 3.2 seconds, and retake-mark.svg is the standalone static vector symbol. Browser rasterization uses system Arial/Helvetica and Courier New; no font files are redistributed. The web template's own typography remains independent of the logo artwork.

Run npm ci here, then render.ps1 on the existing Windows workstation. The script uses the project-local Node executable and writes only these named brand assets. It never submits a cloud render or logs into a provider. It retains the editable composition and package lock. Future visual changes should preserve a new reviewed state before replacing the live page.
