param(
    [Parameter(Position=0,Mandatory=$true)][ValidateSet('init','validate','plan','run')][string]$Command,
    [Parameter(Position=1,Mandatory=$true)][string]$Manifest,
    [ValidateSet('prepare','generate','check','mix','lips','finish','verify')][string]$Through='verify',
    [switch]$Force
)
$retakePython = Join-Path $PSScriptRoot '..\facefusion\.venv\Scripts\python.exe'
$retakeArgs = @((Join-Path $PSScriptRoot 'scene_pipeline.py'), $Command, $Manifest)
if ($Command -eq 'run') {
    $retakeArgs += @('--through', $Through)
    if ($Force) { $retakeArgs += '--force' }
}
& $retakePython @retakeArgs
exit $LASTEXITCODE
