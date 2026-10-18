"""JWT 认证（G6）：请求头 Authorization: Bearer {token}

使用 djangorestframework-simplejwt，扩展自定义返回 401 格式。
"""
from rest_framework_simplejwt.authentication import (
    JWTAuthentication as SimpleJWTAuthentication,
)

from apps.common.constants import UserStatus
from apps.common.exceptions import BizException


class JWTAuthentication(SimpleJWTAuthentication):
    """JWT 认证，额外校验账号是否被禁用"""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user is None:
            from apps.common.exceptions import UnauthorizedError
            raise UnauthorizedError("用户不存在或登录已失效")
        # 禁用账号：1.10 禁用后不能登录
        if user.status != UserStatus.NORMAL:
            from apps.common.exceptions import UnauthorizedError
            raise UnauthorizedError("账号已被禁用，请联系管理员")
        return user
