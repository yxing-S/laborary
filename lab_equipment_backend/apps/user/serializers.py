"""用户模块 Serializer（接口文档 1.1 - 1.12，责任人 A）

对应 Java 项目的 DTO/VO + Bean Validation，DRF Serializer 一体承担。
"""
from rest_framework import serializers

from apps.common.constants import Role, UserStatus
from apps.user.models import User


# ================= 请求 Serializer =================

class UserRegisterSerializer(serializers.Serializer):
    """1.1 用户注册"""

    userNo = serializers.CharField(min_length=1, max_length=50)
    name = serializers.CharField(min_length=1, max_length=50)
    password = serializers.CharField(min_length=6, max_length=30, write_only=True)
    contact = serializers.CharField(max_length=30, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)


class LoginSerializer(serializers.Serializer):
    """1.2 登录"""

    userNo = serializers.CharField(min_length=1)
    password = serializers.CharField(min_length=1, write_only=True)


class ProfileUpdateSerializer(serializers.Serializer):
    """1.4 修改个人资料（userNo、role 不允许修改）"""

    name = serializers.CharField(max_length=50, required=False)
    contact = serializers.CharField(max_length=30, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)


class PasswordUpdateSerializer(serializers.Serializer):
    """1.5 修改个人密码"""

    oldPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(min_length=6, max_length=30, write_only=True)


class ResetPwdBySelfSerializer(serializers.Serializer):
    """1.6 自助重置密码（毕设简化：仅校验学号）"""

    userNo = serializers.CharField(min_length=1)


class AdminUserAddSerializer(serializers.Serializer):
    """1.8 管理员新增用户"""

    userNo = serializers.CharField(min_length=1, max_length=50)
    name = serializers.CharField(min_length=1, max_length=50)
    password = serializers.CharField(min_length=6, max_length=30, write_only=True)
    contact = serializers.CharField(max_length=30, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[Role.ADMIN, Role.USER], default=Role.USER)
    status = serializers.ChoiceField(choices=[UserStatus.NORMAL, UserStatus.DISABLED],
                                    default=UserStatus.NORMAL)


class AdminUserUpdateSerializer(serializers.Serializer):
    """1.9 管理员编辑用户（userNo 不允许修改；密码可选，传了则重置）"""

    name = serializers.CharField(max_length=50, required=False)
    contact = serializers.CharField(max_length=30, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=[Role.ADMIN, Role.USER], required=False)
    status = serializers.ChoiceField(
        choices=[UserStatus.NORMAL, UserStatus.DISABLED], required=False
    )
    password = serializers.CharField(min_length=6, max_length=30, required=False,
                                      write_only=True)


class UserStatusSerializer(serializers.Serializer):
    """1.10 禁用/启用"""

    status = serializers.ChoiceField(choices=[UserStatus.NORMAL, UserStatus.DISABLED])


# ================= 响应 Serializer =================

class UserOutSerializer(serializers.ModelSerializer):
    """用户基础信息（永不返回 password）"""

    userId = serializers.IntegerField(source="id")
    userNo = serializers.CharField(source="user_no")
    createTime = serializers.DateTimeField(source="create_time", format="%Y-%m-%d %H:%M:%S",
                                           required=False)

    class Meta:
        model = User
        fields = ["userId", "userNo", "name", "contact", "department",
                  "role", "status", "createTime"]


class LoginOutSerializer(serializers.Serializer):
    """1.2 登录返回"""

    token = serializers.CharField()
    role = serializers.CharField()
    userId = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()


class ResetPwdOutSerializer(serializers.Serializer):
    """1.6 / 1.11 重置密码返回（新密码仅返回一次）"""

    newPassword = serializers.CharField()
