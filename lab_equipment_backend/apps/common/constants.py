


class Role:
    ADMIN = "admin"
    USER = "user"


class UserStatus:
    NORMAL = "正常"
    DISABLED = "禁用"


class EquipmentStatus:
    """设备状态（7.1 字典）：闲置 / 借出中 / 维修中 / 已报废"""

    IDLE = "闲置"
    BORROWED = "借出中"
    REPAIRING = "维修中"
    SCRAPPED = "已报废"

    ALL = ["闲置", "借出中", "维修中", "已报废"]


class ApprovalStatus:
    """借用审批状态（7.2 字典）"""

    PENDING = "待审批"
    PASSED = "已通过"
    REJECTED = "已驳回"
    CANCELED = "已取消"
    RETURNED = "已归还"

    ALL = ["待审批", "已通过", "已驳回", "已取消", "已归还"]


class OverdueStatus:
    """逾期状态（G12 归 B：定时任务/查询时实时计算，A 只读）"""

    NORMAL = "正常"
    OVERDUE = "已逾期"
    OVERDUE_RETURNED = "逾期已归还"


class ReturnType:
    """确认归还类型（4.3）"""

    NORMAL = "normal"
    DAMAGE = "damage"
    LOSE = "lose"


class AuditResult:
    """审批结果（3.5）"""

    PASS = "pass"
    REJECT = "reject"


# ======================================================================
# ↓↓↓ B 模块兼容层（A 侧维护；B 的代码保持原样不改）↓↓↓
# B 的 borrow/log 代码按另一套常量命名编写，以下补齐其所需名称，
# 取值与现行中文枚举 / 接口文档对齐。
# ======================================================================


class AuditAction:
    """审批动作（B 的 borrow 序列化器用），取值同 AuditResult（3.5：pass/reject）"""

    APPROVE = AuditResult.PASS
    REJECT = AuditResult.REJECT


# B 代码使用的旧别名 → 现行枚举
ApprovalStatus.APPROVED = ApprovalStatus.PASSED      # 已通过
ApprovalStatus.CANCELLED = ApprovalStatus.CANCELED   # 已取消
ReturnType.DAMAGED = ReturnType.DAMAGE               # damage
ReturnType.LOST = ReturnType.LOSE                    # lose


class BizErrorCode:
    """业务错误码（B 的 borrow 模块用）"""

    WRONG_CREDENTIALS = 2001
    ACCOUNT_DISABLED = 2002
    USER_NO_EXISTS = 2003
    EQUIPMENT_NO_EXISTS = 2004
    EQUIPMENT_NOT_AVAILABLE = 2005
    HAS_OVERDUE = 2006
    CANNOT_CANCEL = 2007
    ALREADY_APPROVED = 2008
    CANNOT_RETURN = 2009
    RETURN_ALREADY_SUBMITTED = 2010
    EQUIPMENT_BORROWED = 2011
    UPLOAD_FAILED = 2012
    EXCEL_FORMAT_ERROR = 2013
    ACCOUNT_LOCKED = 2014


class OperationModule:
    """操作日志模块标识（G9，B 的 @log_operation 用）"""

    USER_MANAGEMENT = "USER_MANAGEMENT"
    EQUIPMENT_MANAGEMENT = "EQUIPMENT_MANAGEMENT"
    BORROW_APPLICATION = "BORROW_APPLICATION"
    BORROW_APPROVAL = "BORROW_APPROVAL"
    RETURN_CONFIRM = "RETURN_CONFIRM"
    SYSTEM_SETTING = "SYSTEM_SETTING"


class LogResult:
    """操作日志结果（B 的 log 切面用）"""

    SUCCESS = "成功"
    FAIL = "失败"
