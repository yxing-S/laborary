"""用户/认证模块视图（对齐《后端API接口文档》二、三章）

接口清单：
2.1 POST /auth/register                     用户注册
2.2 POST /auth/login                        用户登录
2.3 POST /auth/logout                       退出登录
2.4 POST /auth/reset-password               密码找回
2.5 PUT  /auth/password                     修改个人密码
3.1 GET  /users/me                          获取当前用户信息
3.2 PUT  /users/me                          修改个人资料
3.3 GET  /admin/users                       用户列表查询
3.4 POST /admin/users                       新增用户
3.5 PUT  /admin/users/{id}                  编辑用户
3.6 PUT  /admin/users/{id}/status           禁用/启用用户
3.7 PUT  /admin/users/{id}/reset-password   强制重置密码
3.8 DELETE /admin/users/{id}                删除用户
3.9 POST /admin/users/import                批量导入用户
3.10 GET  /admin/users/export               导出用户列表
"""
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.constants import BizErrorCode, OperationModule, UserStatus
from apps.common.exceptions import BadRequestError, BizException, NotFoundError
from apps.common.pagination import paginate
from apps.common.permissions import IsAdmin
from apps.common.response import Result
from apps.common.utils import read_excel_sheet, write_excel_sheet
from apps.log.decorators import log_operation
from apps.user.models import User
from apps.user.serializers import (
    AdminResetPasswordSerializer,
    AdminUserAddSerializer,
    AdminUserUpdateSerializer,
    ChangePasswordSerializer,
    LoginOutSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterOutSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserOutSerializer,
    UserStatusSerializer,
)


def _issue_token(user: User):
    """为用户签发 JWT access token，返回 (token, 过期时间戳毫秒)"""
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    return str(access), int(access["exp"] * 1000)


def _get_user_or_404(pk) -> User:
    user = User.objects.filter(pk=pk).first()
    if user is None:
        raise NotFoundError("用户不存在")
    return user


# ================= 2.1 用户注册 =================

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """2.1 用户注册：userNo 唯一；角色固定 user"""
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    if User.objects.filter(user_no=data["userNo"]).exists():
        raise BizException("学号/工号已存在", code=BizErrorCode.USER_NO_EXISTS)

    with transaction.atomic():
        user = User.objects.create_user(
            user_no=data["userNo"],
            name=data["name"],
            password=data["password"],
            contact=data.get("contact", ""),
            department=data.get("department", ""),
        )
    token, expire_at = _issue_token(user)
    out = RegisterOutSerializer({
        "id": user.id,
        "userNo": user.user_no,
        "name": user.name,
        "role": user.role,
        "token": token,
        "expireAt": expire_at,
    })
    return Result.to_response(Result.success(out.data))


# ================= 2.2 用户登录 =================

@api_view(["POST"])
@permission_classes([AllowAny])
@log_operation(module=OperationModule.SYSTEM_SETTING, action="用户登录")
def login(request):
    """2.2 用户登录：返回 token；禁用账号返回 2002"""
    ser = LoginSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    user = User.objects.filter(user_no=data["userNo"]).first()
    if user is None or not user.check_password(data["password"]):
        raise BizException("用户名或密码错误", code=BizErrorCode.WRONG_CREDENTIALS)

    if user.status == UserStatus.DISABLED:
        raise BizException("账号已被禁用，请联系管理员", code=BizErrorCode.ACCOUNT_DISABLED)

    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    token, expire_at = _issue_token(user)
    out = LoginOutSerializer({
        "id": user.id,
        "userNo": user.user_no,
        "name": user.name,
        "role": user.role,
        "contact": user.contact,
        "department": user.department,
        "token": token,
        "expireAt": expire_at,
    })
    return Result.to_response(Result.success(out.data))


# ================= 2.3 退出登录 =================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """2.3 退出登录：无状态 JWT，前端丢弃 token 即可（MVP 简化）"""
    return Result.to_response(Result.success(message="退出登录成功"))


# ================= 2.4 密码找回 =================

@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    """2.4 密码找回（MVP 简化：校验学号后重置为固定初始密码）"""
    ser = ResetPasswordSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user_no = ser.validated_data["userNo"]

    user = User.objects.filter(user_no=user_no).first()
    if user is None:
        raise NotFoundError("该学号/工号不存在")

    new_pwd = "123456"
    user.set_password(new_pwd)
    user.save()
    return Result.to_response(Result.success({"newPassword": new_pwd}, "密码已重置"))


# ================= 2.5 修改个人密码 =================

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """2.5 修改个人密码：校验旧密码"""
    ser = ChangePasswordSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    user = request.user
    if not user.check_password(data["oldPassword"]):
        raise BizException("旧密码错误", code=BizErrorCode.WRONG_CREDENTIALS)
    user.set_password(data["newPassword"])
    user.save()
    return Result.to_response(Result.success(message="密码修改成功"))


# ================= 3.1 获取当前用户信息 =================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_me(request):
    """3.1 从 token 解析当前登录人"""
    return Result.to_response(Result.success(UserOutSerializer(request.user).data))


# ================= 3.2 修改个人资料 =================

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def user_me_update(request):
    """3.2 修改个人资料：userNo、role 不允许修改"""
    ser = ProfileUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    user = request.user
    for field in ("name", "contact", "department"):
        if field in data:
            setattr(user, field, data[field])
    user.save()
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 3.3 用户列表查询 =================

@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_user_list(request):
    """3.3 分页 + 关键字/角色/状态/院系筛选；仅 admin"""
    keyword = (request.query_params.get("keyword") or "").strip()
    role = (request.query_params.get("role") or "").strip()
    status = (request.query_params.get("status") or "").strip()
    department = (request.query_params.get("department") or "").strip()

    qs = User.objects.all().order_by("-id")
    if keyword:
        qs = qs.filter(
            Q(user_no__icontains=keyword) | Q(name__icontains=keyword)
        )
    if role:
        qs = qs.filter(role=role)
    if status:
        qs = qs.filter(status=status)
    if department:
        qs = qs.filter(department__icontains=department)

    return paginate(request, qs, UserOutSerializer)


# ================= 3.4 新增用户 =================

@api_view(["POST"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.USER_MANAGEMENT, action="新增用户")
def admin_user_add(request):
    """3.4 管理员新增用户：含 role"""
    ser = AdminUserAddSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    if User.objects.filter(user_no=data["userNo"]).exists():
        raise BizException("学号/工号已存在", code=BizErrorCode.USER_NO_EXISTS)

    with transaction.atomic():
        user = User.objects.create_user(
            user_no=data["userNo"],
            name=data["name"],
            password=data["password"],
            contact=data.get("contact", ""),
            department=data.get("department", ""),
            role=data.get("role", "user"),
        )
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 3.5 编辑用户 =================

@api_view(["PUT"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.USER_MANAGEMENT, action="编辑用户")
def admin_user_update(request, pk):
    """3.5 管理员编辑用户：userNo 不允许修改"""
    user = _get_user_or_404(pk)
    ser = AdminUserUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    with transaction.atomic():
        for field in ("name", "role", "contact", "department", "status"):
            if field in data:
                setattr(user, field, data[field])
        user.save()
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 3.6 禁用/启用用户 =================

@api_view(["PUT"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.USER_MANAGEMENT, action="禁用/启用用户")
def admin_user_status(request, pk):
    """3.6 禁用后不能登录；历史借用记录保留"""
    user = _get_user_or_404(pk)
    ser = UserStatusSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user.status = ser.validated_data["status"]
    user.save(update_fields=["status", "update_time"])
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 3.7 强制重置密码 =================

@api_view(["PUT"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.USER_MANAGEMENT, action="重置用户密码")
def admin_reset_password(request, pk):
    """3.7 管理员指定新密码并重置"""
    user = _get_user_or_404(pk)
    ser = AdminResetPasswordSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user.set_password(ser.validated_data["newPassword"])
    user.save()
    return Result.to_response(Result.success(message="密码重置成功"))


# ================= 3.8 删除用户 =================

@api_view(["DELETE"])
@permission_classes([IsAdmin])
@log_operation(module=OperationModule.USER_MANAGEMENT, action="删除用户")
def admin_user_delete(request, pk):
    """3.8 逻辑删除（MVP 用禁用代替）：置为 disabled，历史记录保留"""
    user = _get_user_or_404(pk)
    user.status = UserStatus.DISABLED
    user.save(update_fields=["status", "update_time"])
    return Result.to_response(Result.success(message="用户已删除"))


# ================= 3.9 批量导入用户 =================

@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_user_import(request):
    """3.9 form-data 上传 Excel；返回成功/失败明细"""
    file = request.FILES.get("file")
    if not file:
        raise BizException("请上传 Excel 文件", code=BizErrorCode.EXCEL_FORMAT_ERROR)
    if not file.name.endswith((".xlsx", ".xls")):
        raise BizException("仅支持 .xlsx/.xls 格式", code=BizErrorCode.EXCEL_FORMAT_ERROR)

    try:
        headers, rows = read_excel_sheet(file.read())
    except ValueError as exc:
        raise BizException(str(exc), code=BizErrorCode.EXCEL_FORMAT_ERROR)

    success_count = 0
    fail_list = []
    for row in rows:
        user_no = str(row.get("学号/工号", "") or row.get("userNo", "") or "").strip()
        name = str(row.get("姓名", "") or row.get("name", "") or "").strip()
        password = str(row.get("密码", "") or row.get("password", "") or "").strip()
        contact = str(row.get("联系方式", "") or row.get("contact", "") or "").strip()
        department = str(row.get("院系", "") or row.get("department", "") or "").strip()

        if not user_no:
            fail_list.append({"row": row.get("__row__"), "reason": "学号/工号不能为空"})
            continue
        if not name:
            fail_list.append({"row": row.get("__row__"), "userNo": user_no, "reason": "姓名不能为空"})
            continue
        if not password:
            password = "123456"
        if User.objects.filter(user_no=user_no).exists():
            fail_list.append({"row": row.get("__row__"), "userNo": user_no, "name": name,
                              "reason": "学号/工号已存在"})
            continue

        try:
            User.objects.create_user(
                user_no=user_no, name=name, password=password,
                contact=contact, department=department,
            )
            success_count += 1
        except Exception as exc:
            fail_list.append({"row": row.get("__row__"), "userNo": user_no, "name": name,
                              "reason": str(exc)})

    return Result.to_response(Result.success({
        "total": len(rows),
        "successCount": success_count,
        "failCount": len(fail_list),
        "failList": fail_list,
    }))


# ================= 3.10 导出用户列表 =================

@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_user_export(request):
    """3.10 导出用户列表为 Excel"""
    max_rows = getattr(settings, "EXPORT_MAX_ROWS", 10000)
    keyword = (request.query_params.get("keyword") or "").strip()
    role = (request.query_params.get("role") or "").strip()
    status = (request.query_params.get("status") or "").strip()
    department = (request.query_params.get("department") or "").strip()

    qs = User.objects.all().order_by("id")
    if keyword:
        qs = qs.filter(Q(user_no__icontains=keyword) | Q(name__icontains=keyword))
    if role:
        qs = qs.filter(role=role)
    if status:
        qs = qs.filter(status=status)
    if department:
        qs = qs.filter(department__icontains=department)
    qs = qs[:max_rows]

    headers = ["ID", "学号/工号", "姓名", "角色", "联系方式", "所属院系", "账号状态", "创建时间"]
    rows = []
    for u in qs:
        rows.append([
            u.id, u.user_no, u.name, u.role, u.contact, u.department,
            u.status, u.create_time.strftime("%Y-%m-%d %H:%M:%S"),
        ])

    content = write_excel_sheet("用户列表", headers, rows)
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="users.xlsx"'
    return response
