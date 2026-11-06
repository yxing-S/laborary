#!/usr/bin/env bash
# 实验室设备借用管理系统 - 后端一键部署脚本
# 用法：bash deploy/install.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"
SERVICE_NAME="lab-equipment"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> 后端目录：${APP_DIR}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "未找到 ${PYTHON_BIN}，请先安装 Python 3.10+"
    exit 1
fi

# ---------- 1. 虚拟环境与依赖 ----------
if [ ! -d "venv" ]; then
    echo "==> 创建虚拟环境 venv"
    "$PYTHON_BIN" -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip -q
echo "==> 安装 Python 依赖"
pip install -r requirements.txt -q

# ---------- 2. 生成 .env ----------
if [ ! -f .env ]; then
    echo "==> 未发现 .env，请填写数据库与站点信息"
    read -r -p "MySQL 主机 [127.0.0.1]: " DB_HOST
    DB_HOST="${DB_HOST:-127.0.0.1}"
    read -r -p "MySQL 端口 [3306]: " DB_PORT
    DB_PORT="${DB_PORT:-3306}"
    read -r -p "MySQL 用户 [root]: " DB_USER
    DB_USER="${DB_USER:-root}"
    read -r -s -p "MySQL 密码: " DB_PASSWORD
    echo
    read -r -p "MySQL 数据库名 [lab_equipment]: " DB_NAME
    DB_NAME="${DB_NAME:-lab_equipment}"
    read -r -p "ALLOWED_HOSTS [127.0.0.1,localhost,62.234.128.72]: " ALLOWED_HOSTS
    ALLOWED_HOSTS="${ALLOWED_HOSTS:-127.0.0.1,localhost,62.234.128.72}"

    SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
    cat > .env <<EOF
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${ALLOWED_HOSTS}
JWT_ACCESS_MINUTES=720
EOF
    chmod 600 .env
    echo "==> 已生成 .env"
else
    echo "==> 使用已有 .env"
fi

# ---------- 3. 创建数据库（不存在时） ----------
echo "==> 检查并创建数据库"
python - <<'PY'
import environ
import pymysql

env = environ.Env()
env.read_env(".env")

db_name = env("DB_NAME", default="lab_equipment")
conn = pymysql.connect(
    host=env("DB_HOST", default="127.0.0.1"),
    port=env.int("DB_PORT", default=3306),
    user=env("DB_USER", default="root"),
    password=env("DB_PASSWORD", default=""),
    charset="utf8mb4",
)
with conn.cursor() as cursor:
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
        "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
    )
conn.close()
print(f"数据库 {db_name} 已就绪")
PY

# ---------- 4. 建表与管理员账号 ----------
echo "==> 执行数据库迁移"
python manage.py migrate --noinput
echo "==> 初始化管理员账号"
python manage.py seed_admin

# ---------- 5. 注册 systemd 服务并启动 ----------
if [ "$(id -u)" -eq 0 ] && command -v systemctl >/dev/null 2>&1; then
    echo "==> 配置 systemd 服务 ${SERVICE_NAME}"
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Lab Equipment Borrowing System Backend
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn lab_equipment.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME" >/dev/null
    systemctl restart "$SERVICE_NAME"
    sleep 2
    systemctl status "$SERVICE_NAME" --no-pager || true
else
    echo "==> 当前非 root 或无 systemd，请手动启动：bash deploy/start.sh"
fi

echo
echo "部署完成。默认管理员：ADMIN001 / admin123"
echo "后端监听：http://127.0.0.1:8000"
echo "接口前缀：/api/v1（Nginx 将 /real-api 反向代理到本服务）"
