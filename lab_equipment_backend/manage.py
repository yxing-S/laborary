#!/usr/bin/env python
"""Django 管理入口：python manage.py runserver 0.0.0.0:8000"""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lab_equipment.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django，请确认已安装：pip install Django"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
