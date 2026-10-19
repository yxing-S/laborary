"""用户/认证模块 Serializer（对齐《后端API接口文档》二、三章）
"""
from rest_framework import serializers

from apps.common.constants import Role, UserStatus
from apps.user.models import User


# ================= 请求 Serializer =================

class RegisterSerializer(serializers.Serializer):
    """2.1 用户注册"""

    userNo = serializers.CharField(min_length=5, max_length=20)
    name = serializers.CharField(min_length=2, max_length=20)
    password = serializers.CharField(min_length=6, max_length=20, write_only=True)
    contact = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    department = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")


class LoginSerializer(serializers.Serializer):
    """2.2 用户登录"""

    userNo = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ResetPasswordSerializer(serializers.Serializer):
    """2.4 密码找回（MVP 简化）"""

    userNo = serializers.CharField()
    contact = serializers.CharField(required=False, allow_blank=True, default="")


class ChangePasswordSerializer(serializers.Serializer):
    """2.5 修改个人密码"""

    oldPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(min_length=6, max_length=20, write_only=True)


class ProfileUpdateSerializer(serializers.Serializer):
    """3.2 修改个人资料（userNo、role 不允许修改）"""

    name = serializers.CharField(min_length=2, max_length=20, required=False)
    contact = serializers.CharField(max_length=30, required=False, allow_blank=True)
    department = serializers.CharField(max_length=50, required=False, allow_blank=True)


class AdminUserAddSerializer(serializers.Serializer):
    """3.4 管理员新增用户"""

    userNo = serializers.CharField(min_length=5, max_length=20)
    name = serializers.CharField(min_length=2, max_length=20)
    role = serializers.ChoiceField(choices=[Role.ADMIN, Role.USER], default=Role.USER)
    password = serializers.CharField(min_length=6, max_length=20, write_only=True)
    contact = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    department = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")


class AdminUserUpdateSerializer(serializers.Serializer):
    """3.5 管理员编辑用户（userNo 不允许修改）"""

    name = serializers.CharField(min_length=2, max_length=20, required=False)
    role = serializers.ChoiceField(choices=[Role.ADMIN, Role.USER], required=False)
    contact = serializers.CharField(max_length=30, required=False, allow_blank=True)
    department = serializers.CharField(max_length=50, required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=[UserStatus.NORMAL, UserStatus.DISABLED], required=False
    )


class UserStatusSerializer(serializers.Serializer):
    """3.6 禁用/启用用户"""

    status = serializers.ChoiceField(choices=[UserStatus.NORMAL, UserStatus.DISABLED])


class AdminResetPasswordSerializer(serializers.Serializer):
    """3.7 管理员强制重置密码"""

    newPassword = serializers.CharField(min_length=6, max_length=20, write_only=True)


# ================= 响应 Serializer =================

class UserOutSerializer(serializers.ModelSerializer):
    """用户基础信息（永不返回 password）"""

    id = serializers.IntegerField(read_only=True)
    userNo = serializers.CharField(source="user_no")
    lastLoginTime = serializers.DateTimeField(
        source="last_login", format="%Y-%m-%d %H:%M:%S",
        allow_null=True, required=False, read_only=True,
    )
    createTime = serializers.DateTimeField(
        source="create_time", format="%Y-%m-%d %H:%M:%S", read_only=True
    )

    class Meta:
        model = User
        fields = ["id", "userNo", "name", "role", "contact", "department",
                  "status", "lastLoginTime", "createTime"]


class LoginOutSerializer(serializers.Serializer):
    """2.2 登录返回"""

    id = serializers.IntegerField()
    userNo = serializers.CharField()
    name = serializers.CharField()
    role = serializers.CharField()
    contact = serializers.CharField()
    department = serializers.CharField()
    token = serializers.CharField()
    expireAt = serializers.IntegerField()


class RegisterOutSerializer(serializers.Serializer):
    """2.1 注册返回"""

    id = serializers.IntegerField()
    userNo = serializers.CharField()
    name = serializers.CharField()
    role = serializers.CharField()
    token = serializers.CharField()
    expireAt = serializers.IntegerField()


class ResetPasswordOutSerializer(serializers.Serializer):
    """2.4 / 3.7 重置密码返回（新密码仅返回一次）"""

    newPassword = serializers.CharField()
