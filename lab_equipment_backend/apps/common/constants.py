"""公共枚举常量（对齐《后端API接口文档》第十章）

状态值统一使用英文，与接口文档枚举定义 10.1-10.7 一致。
"""


class Role:
    ADMIN = "admin"
    USER = "user"


class UserStatus:
    """账号状态：normal / disabled（10.2）"""

    NORMAL = "normal"
    DISABLED = "disabled"


class EquipmentStatus:
    """设备状态（10.3）：idle / borrowed / repairing / scrapped"""

    IDLE = "idle"
    BORROWED = "borrowed"
    REPAIRING = "repairing"
    SCRAPPED = "scrapped"

    ALL = [IDLE, BORROWED, REPAIRING, SCRAPPED]


class ApprovalStatus:
    """审批状态（10.4）：pending / approved / rejected / returned / cancelled"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"
    CANCELLED = "cancelled"

    ALL = [PENDING, APPROVED, REJECTED, RETURNED, CANCELLED]


class OverdueStatus:
    """逾期状态（10.5）：normal / overdue / overdue_returned"""

    NORMAL = "normal"
    OVERDUE = "overdue"
    OVERDUE_RETURNED = "overdue_returned"


class ReturnType:
    """归还类型（10.6）：normal / damaged / lost"""

    NORMAL = "normal"
    DAMAGED = "damaged"
    LOST = "lost"


class AuditAction:
    """审批动作（6.5）：approve / reject"""

    APPROVE = "approve"
    REJECT = "reject"


class OperationModule:
    """操作日志模块（10.7）"""

    USER_MANAGEMENT = "USER_MANAGEMENT"
    EQUIPMENT_MANAGEMENT = "EQUIPMENT_MANAGEMENT"
    BORROW_APPLICATION = "BORROW_APPLICATION"
    BORROW_APPROVAL = "BORROW_APPROVAL"
    RETURN_CONFIRM = "RETURN_CONFIRM"
    SYSTEM_SETTING = "SYSTEM_SETTING"


class LogResult:
    """操作日志结果（内部使用，不对外暴露）"""

    SUCCESS = "成功"
    FAIL = "失败"


class BizErrorCode:
    """业务错误码（接口文档 1.5 节 2xxx）"""

    WRONG_CREDENTIALS = 2001        # 用户名或密码错误
    ACCOUNT_DISABLED = 2002         # 账号已被禁用
    USER_NO_EXISTS = 2003           # 学号/工号已存在
    EQUIPMENT_NO_EXISTS = 2004      # 设备编号已存在
    EQUIPMENT_NOT_AVAILABLE = 2005  # 该设备当前不可借用
    HAS_OVERDUE = 2006              # 存在逾期未归还记录，禁止新申请
    CANNOT_CANCEL = 2007            # 申请状态不允许取消
    ALREADY_APPROVED = 2008         # 审批已通过，不可撤回
    CANNOT_RETURN = 2009            # 借用状态不允许发起归还
    RETURN_ALREADY_SUBMITTED = 2010  # 归还申请已提交，请勿重复提交
    EQUIPMENT_BORROWED = 2011       # 设备处于借出中，不可手动修改状态
    UPLOAD_FAILED = 2012            # 文件上传失败
    EXCEL_FORMAT_ERROR = 2013       # Excel 导入格式错误
    ACCOUNT_LOCKED = 2014           # 密码错误次数过多，账号已锁定
