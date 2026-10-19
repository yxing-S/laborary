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
