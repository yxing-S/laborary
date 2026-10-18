"""角色权限校验（G7）

"""
from rest_framework.permissions import BasePermission, SAFE_METHODS

from apps.common.constants import Role


class IsAuthenticated(BasePermission):
    """已登录即可（admin/user 均可）"""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdmin(BasePermission):
    """仅管理员"""

    message = "权限不足，无该操作访问权限"

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsAdminOrReadOnly(BasePermission):
    """管理员全部权限，普通用户仅 GET"""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )
