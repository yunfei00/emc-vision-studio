param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Python not found: $python" }
$out = Join-Path $Root "private\lost-signal\phase10\audio"
New-Item -ItemType Directory -Force -Path $out | Out-Null
$timeline = Join-Path $out "timeline.json"
& $python (Join-Path $PSScriptRoot "prepare_phase10_audio.py") --root $Root --repo $repo --mode prepare
if ($LASTEXITCODE -ne 0) { throw "Timeline preparation failed" }
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like "zh-*" })
if ($voices.Count -eq 0) {
    Write-Host "No offline Chinese SAPI voice installed." -ForegroundColor Yellow
    Write-Host "Available voices:"
    $synth.GetInstalledVoices() | ForEach-Object { Write-Host ($_.VoiceInfo.Name + " [" + $_.VoiceInfo.Culture.Name + "]") }
    $synth.Dispose()
    throw "Chinese offline voice missing. Install a Windows Chinese text-to-speech voice and retry; no cloud TTS used."
}
$synth.SelectVoice($voices[0].VoiceInfo.Name)
$synth.Rate = 1
$items = Get-Content -LiteralPath $timeline -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($item in $items) {
    $wav = Join-Path $out ($item.id + ".wav")
    if ((Test-Path $wav) -and ((Get-Item $wav).Length -gt 1000)) { Write-Host ("SKIP " + $item.id); continue }
    Write-Host ("VOICE " + $item.id)
    $synth.SetOutputToWaveFile($wav)
    try { $synth.Speak([string]$item.text) } finally { $synth.SetOutputToNull() }
}
$synth.Dispose()
& $python (Join-Path $PSScriptRoot "prepare_phase10_audio.py") --root $Root --repo $repo --mode mix
if ($LASTEXITCODE -ne 0) { throw "Audio mixing failed" }
Write-Host "Phase 10 offline Chinese voice and music completed."
