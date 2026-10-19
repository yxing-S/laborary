
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `lab_equipment`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

USE `lab_equipment`;

-- ---------------------------------------------------------------------
-- 1. 用户表（域1：A）
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id`         BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `user_no`    VARCHAR(50)  NOT NULL COMMENT '学号/工号，唯一',
    `name`       VARCHAR(50)  NOT NULL COMMENT '姓名',
    `password`   VARCHAR(100) NOT NULL COMMENT 'BCrypt 密文',
    `contact`    VARCHAR(30)  DEFAULT NULL COMMENT '联系方式',
    `department` VARCHAR(100) DEFAULT NULL COMMENT '院系/部门',
    `role`       VARCHAR(20)  NOT NULL DEFAULT 'user' COMMENT '角色：admin/user',
    `status`     VARCHAR(10)  NOT NULL DEFAULT 'normal' COMMENT '账号状态：normal/disabled',
    `create_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_no` (`user_no`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户表（管理员/普通用户）';

-- ---------------------------------------------------------------------
-- 2. 设备表（域1：A；借出中状态只允许 B 的 3.5/4.3 事务改写）
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `equipment`;
CREATE TABLE `equipment` (
    `id`           BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `equipment_no` VARCHAR(50)   NOT NULL COMMENT '设备编号，全局唯一',
    `name`         VARCHAR(100)  NOT NULL COMMENT '设备名称',
    `model`        VARCHAR(100)  DEFAULT NULL COMMENT '型号',
    `spec`         VARCHAR(200)  DEFAULT NULL COMMENT '规格',
    `buy_date`     DATE          DEFAULT NULL COMMENT '购置日期',
    `price`        DECIMAL(10,2) DEFAULT NULL COMMENT '单价（元）',
    `location`     VARCHAR(200)  DEFAULT NULL COMMENT '存放位置',
    `status`       VARCHAR(20)   NOT NULL DEFAULT 'idle'
                   COMMENT '设备状态：idle/borrowed/repairing/scrapped',
    `img_url`      VARCHAR(255)  DEFAULT NULL COMMENT '设备图片路径',
    `remark`       VARCHAR(500)  DEFAULT NULL COMMENT '备注',
    `is_deleted`   TINYINT(1)    NOT NULL DEFAULT 0 COMMENT '逻辑删除：1已删除（历史借用记录保留）',
    `create_time`  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_equipment_no` (`equipment_no`),
    KEY `idx_name` (`name`),
    KEY `idx_location` (`location`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '设备表';

-- ---------------------------------------------------------------------
-- 3. 借用记录表（域2：B；A 仅在 2.2 设备详情中只读）
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `borrow_records`;
CREATE TABLE `borrow_records` (
    `id`                 BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `user_id`            BIGINT       NOT NULL COMMENT '申请人用户ID',
    `equipment_id`       BIGINT       NOT NULL COMMENT '设备ID',
    `plan_borrow_start`  DATETIME     NOT NULL COMMENT '计划借用开始时间',
    `plan_return_time`   DATETIME     NOT NULL COMMENT '计划归还时间',
    `borrow_purpose`     VARCHAR(255) DEFAULT NULL COMMENT '借用用途',
    `remark`             VARCHAR(500) DEFAULT NULL COMMENT '申请备注',
    `approval_status`    VARCHAR(20)  NOT NULL DEFAULT 'pending'
                         COMMENT '审批状态：pending/approved/rejected/cancelled/returned',
    `approval_comment`   VARCHAR(500) DEFAULT NULL COMMENT '审批意见（驳回必填）',
    `auditor_id`         BIGINT       DEFAULT NULL COMMENT '审批人用户ID',
    `audit_time`         DATETIME     DEFAULT NULL COMMENT '审批时间',
    `cancel_time`        DATETIME     DEFAULT NULL COMMENT '取消时间（3.3）',
    `return_apply_time`  DATETIME     DEFAULT NULL COMMENT '发起归还申请时间（4.1）',
    `actual_return_time` DATETIME     DEFAULT NULL COMMENT '实际归还时间（4.3）',
    `return_type`        VARCHAR(20)  DEFAULT NULL COMMENT '归还类型：normal/damaged/lost',
    `damage_desc`        VARCHAR(500) DEFAULT NULL COMMENT '损坏/丢失说明',
    `overdue_status`     VARCHAR(20)  NOT NULL DEFAULT 'normal'
                         COMMENT '逾期状态：normal/overdue/overdue_returned（G12）',
    `extra_info`         TEXT         DEFAULT NULL COMMENT '预留扩展信息',
    `create_time`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_equipment_id` (`equipment_id`),
    KEY `idx_approval_status` (`approval_status`),
    KEY `idx_plan_return_time` (`plan_return_time`),
    KEY `idx_overdue_status` (`overdue_status`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '借用申请/审批/归还记录表';

-- ---------------------------------------------------------------------
-- 4. 操作日志表（G9/6.1：B；切面自动写入）
-- ---------------------------------------------------------------------
DROP TABLE IF EXISTS `operation_log`;
CREATE TABLE `operation_log` (
    `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `operator_id`    BIGINT       DEFAULT NULL COMMENT '操作人用户ID',
    `operator_name`  VARCHAR(50)  DEFAULT NULL COMMENT '操作人姓名',
    `module`         VARCHAR(50)  DEFAULT NULL COMMENT '功能模块',
    `action`         VARCHAR(100) DEFAULT NULL COMMENT '操作行为',
    `request_method` VARCHAR(10)  DEFAULT NULL COMMENT 'HTTP 方法',
    `request_url`    VARCHAR(255) DEFAULT NULL COMMENT '请求路径',
    `request_params` TEXT         DEFAULT NULL COMMENT '请求参数（JSON）',
    `ip`             VARCHAR(50)  DEFAULT NULL COMMENT '操作 IP',
    `result`         VARCHAR(20)  NOT NULL DEFAULT '成功' COMMENT '成功/失败',
    `detail`         TEXT         DEFAULT NULL COMMENT '异常信息/备注',
    `create_time`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_operator_id` (`operator_id`),
    KEY `idx_module` (`module`),
    KEY `idx_create_time` (`create_time`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '系统操作日志表';

-- ---------------------------------------------------------------------
-- 初始化默认管理员：学号/工号 admin，密码 admin123（BCrypt）
-- 登录后请尽快通过 1.5 修改密码接口更换
-- ---------------------------------------------------------------------
INSERT INTO `users` (`user_no`, `name`, `password`, `contact`, `department`, `role`, `status`)
VALUES (
    'admin',
    '系统管理员',
    '$2b$12$fD3xgYvdFmJ2y/ng1J2yXexaM7jbOspYe9L/HJTrGrKNwKIvChqW.',
    NULL,
    '实验室管理中心',
    'admin',
    'normal'
);
