#!/usr/bin/env bash
# 停止后端：优先使用 systemd，否则按进程名结束
set -euo pipefail
if command -v systemctl >/dev/null 2>&1 && systemctl status lab-equipment >/dev/null 2>&1; then
    systemctl stop lab-equipment
else
    pkill -f "gunicorn lab_equipment.wsgi:application" || true
fi
echo "后端已停止"
