#!/usr/bin/env bash
# 前台启动后端（调试或未配置 systemd 时使用）
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"
# shellcheck disable=SC1091
source venv/bin/activate
exec gunicorn lab_equipment.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
