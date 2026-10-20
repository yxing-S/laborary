"""
Django 全局配置（G1 脚手架）
对应分工方案：公共基础层 — 项目脚手架、依赖、分层结构（A 牵头）
"""
import environ
from datetime import timedelta
from pathlib import Path

# ---------------- 路径 ----------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------- 环境变量 ----------------
env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env" if (BASE_DIR / ".env").exists() else None)

SECRET_KEY = env("SECRET_KEY", default="lab-equipment-django-insecure-secret-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# ---------------- 应用注册 ----------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方
    "rest_framework",
    "corsheaders",
    # 本项目 apps
    "apps.common",
    "apps.user",
    "apps.equipment",
    # A 的 user 模块用 @log_operation 记录操作日志，依赖 B 的 log 切面
    "apps.log",
]

# ---------------- 中间件 ----------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lab_equipment.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "lab_equipment.asgi.application"
WSGI_APPLICATION = "lab_equipment.wsgi.application"

# ---------------- 数据库（G2：默认 MySQL 8）----------------
DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default="mysql://root:root@localhost:3306/lab_equipment",
    )
    if "DATABASE_URL" in env.ENVIRON
    else {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "lab_equipment",
        "USER": "root",
        "PASSWORD": "root",
        "HOST": "localhost",
        "PORT": "3306",
    }
}

# ---------------- 密码校验（G8 BCrypt）----------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptPasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_USER_MODEL = "user.User"  # 自定义用户模型

# ---------------- 国际化 ----------------
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = False  # 接口文档时间格式 yyyy-MM-dd HH:mm:ss，保持 naive

# ---------------- 静态文件 ----------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------- CORS（前后端分离）----------------
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# ---------------- DRF 配置 ----------------
REST_FRAMEWORK = {
    # 统一返回格式由自定义 renderer 处理（G3）
    "DEFAULT_RENDERER_CLASSES": (
        "apps.common.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    # 认证：JWT（G6）
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.common.authentication.JWTAuthentication",
    ),
    # 权限：默认要求登录（G7，第 9 节第 1 条）
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # 全局异常处理（G4）
    "EXCEPTION_HANDLER": "apps.common.exception_handler.custom_exception_handler",
    # 分页（G5）
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    # 时间格式
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M:%S",
    "DATE_FORMAT": "%Y-%m-%d",
}

# ---------------- SimpleJWT 配置（G6）----------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_MINUTES", default=720)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ---------------- 业务参数 ----------------
EXPORT_MAX_ROWS = 10000  # 5.3 导出最大条数
