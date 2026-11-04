# equipment 表 — 数据库变更记录

## 变更 1

- 类型：字段修改
- 修改日期：2026-10-19 19:07:36
- 修改人：767seven
- 说明：`status` 设备状态值由中文改为英文（idle/borrowed/repairing/scrapped），与 API 文档枚举定义 10.3 一致

```sql
ALTER TABLE `equipment`
    MODIFY `status` VARCHAR(20) NOT NULL DEFAULT 'idle'
    COMMENT '设备状态：idle/borrowed/repairing/scrapped';

-- 存量数据迁移
UPDATE `equipment` SET `status` = 'idle'      WHERE `status` = '闲置';
UPDATE `equipment` SET `status` = 'borrowed'  WHERE `status` = '借出中';
UPDATE `equipment` SET `status` = 'repairing' WHERE `status` = '维修中';
UPDATE `equipment` SET `status` = 'scrapped'  WHERE `status` = '已报废';
```

## 变更 2

- 类型：表删除（重建）
- 修改日期：2026-11-02 20:11:29
- 修改人：767seven
- 说明：按 `sql/schema.sql` 重建本地 `lab_equipment` 库，删除并重建 `equipment` 表。原 2 条设备数据清空，重建前已备份至 `C:\Users\Chen\Desktop\lab_equipment_backup_20261102_200747.sql`

```sql
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `equipment`;
-- 随后执行 sql/schema.sql 中的 CREATE TABLE `equipment` ...（结构见该文件）

SET FOREIGN_KEY_CHECKS = 1;
```
