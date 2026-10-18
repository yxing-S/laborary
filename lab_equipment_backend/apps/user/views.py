"""用户模块视图（接口文档 1.1 - 1.12，责任人 A）

接口清单：
1.1  POST /api/user/register           用户注册
1.2  POST /api/user/login              用户登录
1.3  GET  /api/user/info               获取当前用户信息
1.4  PUT  /api/user/profile            修改个人资料
1.5  PUT  /api/user/password           修改个人密码
1.6  PUT  /api/user/resetPwdBySelf     密码找回（重置密码）
1.7  GET  /api/admin/user/list         管理员-用户列表
1.8  POST /api/admin/user/add          管理员-新增用户
1.9  PUT  /api/admin/user/update/{id}  管理员-编辑用户
1.10 PUT  /api/admin/user/status/{id}  管理员-禁用/启用账号
1.11 PUT  /api/admin/user/resetPwd/{id} 管理员-强制重置密码
1.12 POST /api/admin/user/import       管理员-批量导入用户
"""
import secrets

from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.exceptions import (
    BadRequestError,
    NotFoundError,
)
from apps.common.permissions import IsAdmin
from apps.common.response import Result
from apps.common.utils import read_excel_sheet
from apps.user.models import User
from apps.user.serializers import (
    AdminUserAddSerializer,
    AdminUserUpdateSerializer,
    LoginOutSerializer,
    LoginSerializer,
    PasswordUpdateSerializer,
    ProfileUpdateSerializer,
    ResetPwdBySelfSerializer,
    UserOutSerializer,
    UserRegisterSerializer,
    UserStatusSerializer,
)


def _generate_token(user: User) -> str:
    """为用户签发 JWT access token"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


# ================= 1.1 用户注册 =================

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """1.1 用户注册：userNo 唯一；密码后端加密；角色固定 user"""
    ser = UserRegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    if User.objects.filter(user_no=data["userNo"]).exists():
        raise BadRequestError("学号/工号已存在，请勿重复注册")

    with transaction.atomic():
        user = User.objects.create_user(
            user_no=data["userNo"],
            name=data["name"],
            password=data["password"],
            contact=data.get("contact", ""),
            department=data.get("department", ""),
        )
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 1.2 用户登录 =================

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """1.2 用户登录：返回 token/role/userId/name/status；禁用账号返回 400"""
    ser = LoginSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    user = User.objects.filter(user_no=data["userNo"]).first()
    if user is None or not user.check_password(data["password"]):
        raise BadRequestError("学号/工号或密码错误")

    if user.status == "禁用":
        raise BadRequestError("账号已被禁用，请联系管理员")

    token = _generate_token(user)
    out = LoginOutSerializer({
        "token": token,
        "role": user.role,
        "userId": user.id,
        "name": user.name,
        "status": user.status,
    })
    return Result.to_response(Result.success(out.data))


# ================= 1.3 获取当前登录用户信息 =================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_info(request):
    """1.3 从 token 解析当前登录人"""
    return Result.to_response(Result.success(UserOutSerializer(request.user).data))


# ================= 1.4 修改个人资料 =================

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """1.4 修改个人资料：userNo、role 不允许修改"""
    ser = ProfileUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    user = request.user
    for field in ("name", "contact", "department"):
        if field in data:
            setattr(user, field, data[field])
    user.save()
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 1.5 修改个人密码 =================

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_password(request):
    """1.5 修改个人密码：校验旧密码"""
    ser = PasswordUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    user = request.user
    if not user.check_password(data["oldPassword"]):
        raise BadRequestError("旧密码错误")
    user.set_password(data["newPassword"])
    user.save()
    return Result.to_response(Result.success(msg="密码修改成功"))


# ================= 1.6 密码找回（重置密码）=================

@api_view(["PUT"])
@permission_classes([AllowAny])
def reset_pwd_by_self(request):
    """1.6 毕设简化：仅校验学号，重置为固定初始密码"""
    ser = ResetPwdBySelfSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user_no = ser.validated_data["userNo"]

    user = User.objects.filter(user_no=user_no).first()
    if user is None:
        raise NotFoundError("该学号/工号不存在")

    new_pwd = "123456"
    user.set_password(new_pwd)
    user.save()
    return Result.to_response(Result.success({"newPassword": new_pwd}, "密码已重置为初始密码"))


# ================= 1.7 管理员-用户列表 =================

@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_user_list(request):
    """1.7 分页 + 按学号/院系筛选；仅 admin"""
    page = int(request.query_params.get("page", 1))
    size = int(request.query_params.get("size", 10))
    user_no = request.query_params.get("userNo", "")
    department = request.query_params.get("department", "")
    name = request.query_params.get("name", "")

    qs = User.objects.all().order_by("-id")
    if user_no:
        qs = qs.filter(user_no__icontains=user_no)
    if name:
        qs = qs.filter(name__icontains=name)
    if department:
        qs = qs.filter(department__icontains=department)

    total = qs.count()
    records = qs[(page - 1) * size: page * size]
    pages = (total + size - 1) // size if size > 0 else 0
    return Result.to_response(Result.success({
        "total": total,
        "pages": pages,
        "current": page,
        "records": UserOutSerializer(records, many=True).data,
    }))


# ================= 1.8 管理员-新增用户 =================

@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_user_add(request):
    """1.8 管理员新增用户：含 role、status"""
    ser = AdminUserAddSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    if User.objects.filter(user_no=data["userNo"]).exists():
        raise BadRequestError("学号/工号已存在")

    with transaction.atomic():
        user = User.objects.create_user(
            user_no=data["userNo"],
            name=data["name"],
            password=data["password"],
            contact=data.get("contact", ""),
            department=data.get("department", ""),
            role=data.get("role", "user"),
            status=data.get("status", "正常"),
        )
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 1.9 管理员-编辑用户 =================

@api_view(["PUT"])
@permission_classes([IsAdmin])
def admin_user_update(request, pk):
    """1.9 管理员编辑用户：userNo 不允许修改"""
    user = _get_user_or_404(pk)
    ser = AdminUserUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    with transaction.atomic():
        for field in ("name", "contact", "department", "role", "status"):
            if field in data:
                setattr(user, field, data[field])
        if data.get("password"):
            user.set_password(data["password"])
        user.save()
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 1.10 管理员-禁用/启用账号 =================

@api_view(["PUT"])
@permission_classes([IsAdmin])
def admin_user_status(request, pk):
    """1.10 禁用后不能登录；历史借用记录保留；禁止新建申请"""
    user = _get_user_or_404(pk)
    ser = UserStatusSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user.status = ser.validated_data["status"]
    user.save()
    return Result.to_response(Result.success(UserOutSerializer(user).data))


# ================= 1.11 管理员-强制重置密码 =================

@api_view(["PUT"])
@permission_classes([IsAdmin])
def admin_reset_pwd(request, pk):
    """1.11 返回新的初始密码（仅返回一次）"""
    user = _get_user_or_404(pk)
    new_pwd = secrets.token_hex(4)  # 8 位随机初始密码
    user.set_password(new_pwd)
    user.save()
    return Result.to_response(Result.success({"newPassword": new_pwd}))


# ================= 1.12 管理员-批量导入用户 =================

@api_view(["POST"])
@permission_classes([IsAdmin])
def admin_user_import(request):
    """1.12 form-data 上传 Excel；返回成功/失败条数与失败行信息"""
    file = request.FILES.get("file")
    if not file:
        raise BadRequestError("请上传 Excel 文件")
    if not file.name.endswith((".xlsx",)):
        raise BadRequestError("仅支持 .xlsx 格式")

    headers, rows = read_excel_sheet(file.read())

    success_count = 0
    fail_rows = []
    for row in rows:
        user_no = str(row.get("学号/工号", "") or row.get("userNo", "") or "").strip()
        name = str(row.get("姓名", "") or row.get("name", "") or "").strip()
        password = str(row.get("密码", "") or row.get("password", "") or "").strip()
        contact = str(row.get("联系方式", "") or row.get("contact", "") or "").strip()
        department = str(row.get("院系", "") or row.get("department", "") or "").strip()

        if not user_no:
            fail_rows.append({"row": row.get("__row__"), "reason": "学号/工号不能为空"})
            continue
        if not name:
            fail_rows.append({"row": row.get("__row__"), "userNo": user_no, "reason": "姓名不能为空"})
            continue
        if not password:
            password = "123456"  # 缺省密码

        if User.objects.filter(user_no=user_no).exists():
            fail_rows.append({"row": row.get("__row__"), "userNo": user_no, "reason": "学号/工号已存在"})
            continue

        try:
            User.objects.create_user(
                user_no=user_no, name=name, password=password,
                contact=contact, department=department,
            )
            success_count += 1
        except Exception as e:
            fail_rows.append({"row": row.get("__row__"), "userNo": user_no, "reason": str(e)})

    return Result.to_response(Result.success({
        "successCount": success_count,
        "failCount": len(fail_rows),
        "failRows": fail_rows,
    }))


# ================= 辅助函数 =================

def _get_user_or_404(pk: int) -> User:
    user = User.objects.filter(pk=pk).first()
    if user is None:
        raise NotFoundError("用户不存在")
    return user
