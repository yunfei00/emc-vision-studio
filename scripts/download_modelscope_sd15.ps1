param([string]$Root = "D:\AI-Video")
$ErrorActionPreference = "Stop"
$dir = Join-Path $Root "ComfyUI\models\checkpoints"
if (-not (Test-Path $dir)) { throw "Model directory not found: $dir" }
$file = "v1-5-pruned-emaonly.ckpt"
$url = "https://modelscope.cn/api/v1/models/AI-ModelScope/stable-diffusion-v1-5/repo?Revision=master&FilePath=v1-5-pruned-emaonly.ckpt"
$out = Join-Path $dir $file
$part = "$out.part"
if ((Test-Path $out) -and ((Get-Item $out).Length -gt 3500000000)) { Write-Host "MODEL ALREADY PRESENT: $out"; exit 0 }
Write-Host "Downloading from ModelScope (China). Expected file size about 4GB."
Write-Host "Partial file: $part"
& curl.exe --fail --location --retry 6 --retry-delay 4 --connect-timeout 20 --speed-time 60 --speed-limit 10240 --continue-at - --output $part $url
if ($LASTEXITCODE -ne 0) { throw "Download interrupted or stalled. Partial file preserved; rerun to resume. curl exit code $LASTEXITCODE" }
if ((Get-Item $part).Length -lt 3500000000) { throw "File smaller than expected. Not promoting to model file." }
Move-Item $part $out -Force
Write-Host "DOWNLOAD COMPLETE: $out"
Write-Host "Restart ComfyUI, then run generate_first_image.ps1 -Model modelscope"
