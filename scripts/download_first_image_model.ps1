param(
  [string]$Root = "D:\AI-Video",
  [ValidateSet("mirror","official")][string]$Source = "mirror"
)
$ErrorActionPreference = "Stop"
$dir = Join-Path $Root "ComfyUI\models\checkpoints"
if (-not (Test-Path $dir)) { throw "Checkpoint directory not found: $dir" }
if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) { throw "curl.exe not found on this Windows system" }
$file = "v1-5-pruned-emaonly-fp16.safetensors"
$repo = "Comfy-Org/stable-diffusion-v1-5-archive"
$base = if ($Source -eq "mirror") { "https://hf-mirror.com" } else { "https://huggingface.co" }
$url = "$base/$repo/resolve/main/$file"
$out = Join-Path $dir $file
$part = "$out.part"
if (Test-Path $out) {
  if ((Get-Item $out).Length -gt 1000000000) { Write-Host "FILE EXISTS: $out"; exit 0 }
  throw "Existing target file is suspiciously small: $out"
}
Write-Host "SOURCE: $Source"
Write-Host "URL: $url"
Write-Host "PARTIAL FILE: $part"
Write-Host "Resume is attempted with HTTP Range. Re-run this script after interruptions."
& curl.exe --fail --location --retry 5 --retry-delay 5 --connect-timeout 30 --continue-at - --output $part $url
if ($LASTEXITCODE -ne 0) { throw "Download interrupted. Keep .part and rerun the same command. curl exit code: $LASTEXITCODE" }
$size = (Get-Item $part).Length
if ($size -lt 1000000000) { throw "Downloaded file too small ($size bytes). Keep .part and check URL/content." }
Move-Item -Path $part -Destination $out
Write-Host "DOWNLOAD COMPLETE: $out"
Write-Host "SIZE BYTES: $size"
