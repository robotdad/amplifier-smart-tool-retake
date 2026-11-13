$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $retakeNode = Join-Path $PSScriptRoot 'node_modules\node\bin\node.exe'
    if (-not (Test-Path -LiteralPath $retakeNode)) { throw 'Run npm ci in site/artwork first.' }
    & $retakeNode node_modules/hyperframes/bin/hyperframes.mjs render . --output ../assets/retake-loop.mp4 --fps 30 --workers 2 --quality standard --no-best-effort
    if ($LASTEXITCODE -ne 0) { throw 'HyperFrames render failed.' }
    & ffmpeg -v error -y -ss 3.2 -i ../assets/retake-loop.mp4 -frames:v 1 ../assets/retake-static.png
    if ($LASTEXITCODE -ne 0) { throw 'Static export failed.' }
    & ffmpeg -v error -y -i ../assets/retake-loop.mp4 -filter_complex 'fps=15,scale=1000:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff:max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3' -loop 0 ../assets/retake-loop.gif
    if ($LASTEXITCODE -ne 0) { throw 'GIF export failed.' }
} finally { Pop-Location }
