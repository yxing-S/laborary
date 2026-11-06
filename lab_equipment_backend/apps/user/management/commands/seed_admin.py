"""初始化默认管理员账号（可重复执行，已存在则重置密码与角色）

用法：
    python manage.py seed_admin
    python manage.py seed_admin --user-no admin --password admin123
"""
from django.core.management.base import BaseCommand

from apps.common.constants import Role, UserStatus
from apps.user.models import User


class Command(BaseCommand):
    help = "创建或重置默认管理员账号"

    def add_arguments(self, parser):
        parser.add_argument("--user-no", default="ADMIN001", help="学号/工号")
        parser.add_argument("--password", default="admin123", help="登录密码")
        parser.add_argument("--name", default="系统管理员", help="姓名")

    def handle(self, *args, **options):
        user_no = options["user_no"].strip()
        password = options["password"]
        name = options["name"].strip()

        user, created = User.objects.get_or_create(
            user_no=user_no,
            defaults={"name": name},
        )
        user.name = name
        user.role = Role.ADMIN
        user.status = UserStatus.NORMAL
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "已创建" if created else "已更新"
        self.stdout.write(self.style.SUCCESS(
            f"管理员{action}：{user_no} / {password}"
        ))
