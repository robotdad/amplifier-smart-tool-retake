# Retake website

Retake uses the Amplifier Smart Tools family page template requested through the catalog. The canonical theme is vendored unchanged from microsoft/amplifier-smart-tools at 6f0d00c987eeaf9b56b142d74fd5738888c5686a. The catalog inspected was microsoft/amplifier-smart-tools-catalog at fa4a1de8b2112f920ba39a382d83787c365cec02. Theme code is MIT licensed; its LICENSE remains in site/theme. Exact copied-file hashes are in theme-source.json.

site.json owns product content. build.py is a small local content adapter around the canonical renderer. It supplies Retake's identity without changing the shared family registry, replaces generic installation claims with actual current readiness, and attaches the motion asset to the existing pause/reduced-motion behavior. Shared navigation, attribution, typography, paper palette, layout and gold family mark are preserved. Product-specific CSS is in assets/retake.css. Never patch the vendored shared theme for a Retake-only content change.

## Build and preview

From the repository root with Python 3.12 and site/requirements.txt installed:

```sh
python site/build.py
python -m unittest discover -s site/tests -v
python -m http.server 8000 --directory _site --bind 127.0.0.1
```

On the existing Ducasse environment, ..\facefusion\.venv\Scripts\python.exe already has the required PyYAML version. Generated _site and review screenshots under .work stay out of Git. No GPU model runtime is required to build the page.

To update the theme, obtain the canonical source, run its site/sync_theme.py against this checkout, review the diff, update theme-source.json and rerun checks. The canonical source is a reference checkout, not a runtime network dependency.

## Motion identity

The editable HTML/SVG/GSAP composition is in artwork/index.html and the standalone static symbol is assets/retake-mark.svg. The R's counter evokes a speech balloon, and its red leg is the replacement stroke. The six-second loop strikes out Old line and substitutes New line, while the frame and wordmark remain fixed. Static PNG selects the completed New line state. This is brand artwork, not product demo footage.

HyperFrames 0.8.33 and GSAP 3.14.2 render the composition locally. A project-local Node 22.23.5 is pinned because the workstation's global Node 20 is too old for this renderer. Node_modules is ignored. npm ci in artwork reproduces the dependencies, and render.ps1 renders/converts the assets. These tools are not dependencies of the website build itself.

See artwork/README.md and artwork/provenance.json for the exact source, commands, output hashes and design history. The first generated clapperboard candidate was rejected and is not part of the site. The selected direction was authored directly for HyperFrames after the user requested Unfold or HyperFrames; no model-backed Unfold session or provider call produced this artwork.

## GitHub Pages

The repository was made public by explicit user instruction after GitHub rejected private-repository Pages under the current plan. Pages now uses GitHub Actions. .github/workflows/website.yml builds and uploads a preview artifact for site pushes/pull requests. Deployment requires a manual Website run on main with publish=true, so routine commits do not replace the live page without an explicit publish action.

```sh
gh workflow run website.yml --ref main -f publish=true
```

The expected site is https://robotdad.github.io/amplifier-smart-tool-retake/. Verify the exact workflow/deployed revision and the resulting page before reporting publication complete. The page contains no film excerpts, source-library paths or private credentials. It does not claim the unimplemented smart-agent preparation layer is ready or that Retake is already listed in the catalog.

## Browser checks

artwork/check-site.mjs launches an isolated local Chrome session against _site and checks 1440, 768 and 390 pixel widths, runtime/resource errors, pause behavior, reduced-motion fallback and static behavior with JavaScript disabled. Screenshots and browser-check.json go into .work/site-review. It uses the installed Windows Chrome path and is a local test, not a portable CI requirement.
