param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$dir = Join-Path $Root "ComfyUI\models\checkpoints"
if (-not (Test-Path $dir)) { throw "Checkpoint directory not found: $dir" }
$url = "https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/resolve/main/v1-5-pruned-emaonly-fp16.safetensors"
$out = Join-Path $dir "v1-5-pruned-emaonly-fp16.safetensors"
if (Test-Path $out) { Write-Host "Model file exists: $out"; exit 0 }
Write-Host "Downloading model (~2GB) to $out"
$part = "$out.part"
try {
  Invoke-WebRequest -Uri $url -OutFile $part -MaximumRedirection 10 -UseBasicParsing
  if ((Get-Item $part).Length -lt 1000000000) { throw "Downloaded file is too small; verify model URL/access." }
  Move-Item -Path $part -Destination $out
  Write-Host "DOWNLOAD COMPLETE: $out"
} catch {
  Write-Host "Download failed; partial file retained at $part"
  throw
}
