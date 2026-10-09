$ErrorActionPreference = 'Stop'
Write-Host '=== Windows ==='
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,OSArchitecture | Format-List
Write-Host '=== RAM (GB) ==='
[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
Write-Host '=== NVIDIA GPU ==='
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
  & nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv
} else { Write-Warning 'nvidia-smi not found' }
Write-Host '=== Python / Git ==='
python --version
git --version
Write-Host '=== Disk ==='
Get-PSDrive -PSProvider FileSystem | Select-Object Name,Free,Used | Format-Table
