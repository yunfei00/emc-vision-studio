#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' '=== GPU ==='
if command -v nvidia-smi >/dev/null 2>&1; then nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free --format=csv; else echo 'nvidia-smi unavailable'; fi
printf '%s\n' '=== OS ==='
if [ -f /etc/os-release ]; then grep -E '^(NAME|VERSION)=' /etc/os-release; fi
printf '%s\n' '=== Python ==='
python3 --version || true
printf '%s\n' '=== Disk ==='
df -h .
