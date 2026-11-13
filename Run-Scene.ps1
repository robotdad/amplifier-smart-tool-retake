param(
    [Parameter(Position=0,Mandatory=$true)][ValidateSet('init','validate','plan','run')][string]$Command,
    [Parameter(Position=1,Mandatory=$true)][string]$Manifest,
    [ValidateSet('prepare','generate','check','mix','lips','finish','verify')][string]$Through='verify',
    [switch]$Force
)
$pipelinePython = Join-Path $PSScriptRoot '..\facefusion\.venv\Scripts\python.exe'
$pipelineArgs = @((Join-Path $PSScriptRoot 'scene_pipeline.py'), $Command, $Manifest)
if ($Command -eq 'run') {
    $pipelineArgs += @('--through', $Through)
    if ($Force) { $pipelineArgs += '--force' }
}
& $pipelinePython @pipelineArgs
exit $LASTEXITCODE
