"""用户模型（域 1：身份与资产，责任人 A）

自定义 User 模型，继承 AbstractBaseUser 以便：
- 使用学号 user_no 登录（而非 username）
- 集成 role/status 等业务字段
- 复用 Django 的密码加密（BCrypt，G8）与 session/JWT 认证
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from apps.common.constants import Role, UserStatus
from apps.common.models import TimestampMixin


class UserManager(BaseUserManager):
    """自定义用户管理器"""

    def create_user(self, user_no, name, password, **extra):
        if not user_no:
            raise ValueError("学号/工号不能为空")
        extra.setdefault("role", Role.USER)
        extra.setdefault("status", UserStatus.NORMAL)
        user = self.model(user_no=user_no, name=name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_no, name, password, **extra):
        extra["role"] = Role.ADMIN
        extra["status"] = UserStatus.NORMAL
        return self.create_user(user_no, name, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimestampMixin):
    """用户表（对应 SQL: user）"""

    user_no = models.CharField("学号/工号", max_length=50, unique=True, db_index=True)
    name = models.CharField("姓名", max_length=50)
    password = models.CharField("密码(BCrypt)", max_length=128)
    contact = models.CharField("联系方式", max_length=30, blank=True, default="")
    department = models.CharField("院系/部门", max_length=100, blank=True, default="")
    role = models.CharField(
        "角色", max_length=20, default=Role.USER, db_index=True
    )
    status = models.CharField(
        "账号状态", max_length=10, default=UserStatus.NORMAL
    )

    # Django admin/DRF 需要的字段
    is_active = models.BooleanField(default=True, editable=False)
    is_staff = models.BooleanField(default=False, editable=False)

    USERNAME_FIELD = "user_no"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        db_table = "user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.user_no} - {self.name}"

    # ---- 权限相关：本系统通过 role 字段做 RBAC，不使用 Django 内置 group/permission ----
    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_disabled(self) -> bool:
        return self.status == UserStatus.DISABLED
