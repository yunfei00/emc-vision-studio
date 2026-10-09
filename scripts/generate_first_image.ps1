param([string]$Root = "D:\AI-Video", [string]$Server = "http://127.0.0.1:8188")
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$workflowPath = Join-Path $repo "workflows\text-to-image\first-lab-sd15-api.json"
$modelPath = Join-Path $Root "ComfyUI\models\checkpoints\v1-5-pruned-emaonly-fp16.safetensors"
if (-not (Test-Path $modelPath)) { throw "Model not found: $modelPath. Run download_first_image_model.ps1 first." }
$workflow = Get-Content -Raw -Encoding UTF8 $workflowPath | ConvertFrom-Json
$body = @{prompt=$workflow;client_id="emc-vision-studio"} | ConvertTo-Json -Depth 30
try {
  $response = Invoke-RestMethod -Method Post -Uri "$Server/prompt" -ContentType "application/json" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
  if ($response.error) { throw ($response.error | ConvertTo-Json -Depth 10) }
  Write-Host "QUEUE SUBMITTED: $($response.prompt_id)"
  Write-Host "Check output directory: $(Join-Path $Root 'ComfyUI\output')"
} catch {
  Write-Host "Submission failed. Make sure ComfyUI is running on port 8188 and restart it after adding the model."
  throw
}
