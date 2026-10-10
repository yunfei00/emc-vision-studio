param(
    [string]$Root = "D:\AI-Video",
    [string]$Voice = "",
    [string]$Music = ""
)
$ErrorActionPreference = "Stop"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$argsList = @((Join-Path $PSScriptRoot "make_phase10_audio_subtitles.py"), "--root", $Root, "--repo", $repo)
if ($Voice) { $argsList += @("--voice", $Voice) }
if ($Music) { $argsList += @("--music", $Music) }
& $python @argsList
if ($LASTEXITCODE -ne 0) { throw "Phase 10 export failed: $LASTEXITCODE" }
