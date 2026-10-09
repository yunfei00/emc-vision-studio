#!/usr/bin/env bash
set -euo pipefail
if [ ! -f main.py ]; then echo 'Run this from a tested ComfyUI checkout'; exit 2; fi
python main.py --listen 127.0.0.1 --port 8188
