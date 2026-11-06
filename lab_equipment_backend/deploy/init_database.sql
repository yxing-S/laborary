-- 在服务器 MySQL 中执行（或用宝塔 phpMyAdmin 导入）
-- 数据库名需与 .env 中的 DB_NAME 保持一致
CREATE DATABASE IF NOT EXISTS `lab_equipment`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;
