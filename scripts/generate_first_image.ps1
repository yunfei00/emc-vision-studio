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
$python = Join-Path $Root ".venv\Scripts\python.exe"
$monitor = Join-Path $PSScriptRoot "monitor_comfy_prompt.py"
if (-not (Test-Path $modelPath)) { throw "Model not found: $modelPath" }
if (-not (Test-Path $python)) { throw "Python not found: $python" }
$workflow = Get-Content -Raw -Encoding UTF8 $workflowPath | ConvertFrom-Json
$workflow.'1'.inputs.ckpt_name = $filename
$body = @{prompt=$workflow;client_id="emc-vision-studio"} | ConvertTo-Json -Depth 30
$response = Invoke-RestMethod -Method Post -Uri "$Server/prompt" -ContentType "application/json" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
if ($response.error) { throw ($response.error | ConvertTo-Json -Depth 10) }
if (-not $response.prompt_id) { throw "No prompt_id in ComfyUI response" }
Write-Host "QUEUE SUBMITTED: $($response.prompt_id)"
Write-Host "Waiting for completion or full exception traceback..."
& $python $monitor --server $Server --prompt-id $response.prompt_id --timeout 600
if ($LASTEXITCODE -ne 0) { throw "ComfyUI generation failed or timed out. Monitor exit code: $LASTEXITCODE" }
