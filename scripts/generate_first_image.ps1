param(
  [string]$Root = "D:\AI-Video",
  [string]$Server = "http://127.0.0.1:8188",
  [ValidateSet("modelscope","hf")][string]$Model = "modelscope"
)
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$workflowPath = Join-Path $repo "workflows\text-to-image\first-lab-sd15-api.json"
$filename = if ($Model -eq "modelscope") { "v1-5-pruned-emaonly.ckpt" } else { "v1-5-pruned-emaonly-fp16.safetensors" }
$modelPath = Join-Path (Join-Path $Root "ComfyUI\models\checkpoints") $filename
if (-not (Test-Path $modelPath)) { throw "Model not found: $modelPath" }
$workflow = Get-Content -Raw -Encoding UTF8 $workflowPath | ConvertFrom-Json
$workflow.'1'.inputs.ckpt_name = $filename
$body = @{prompt=$workflow;client_id="emc-vision-studio"} | ConvertTo-Json -Depth 30
$response = Invoke-RestMethod -Method Post -Uri "$Server/prompt" -ContentType "application/json" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
if ($response.error) { throw ($response.error | ConvertTo-Json -Depth 10) }
Write-Host "QUEUE SUBMITTED: $($response.prompt_id)"
Write-Host "Check actual result in ComfyUI output directory."
