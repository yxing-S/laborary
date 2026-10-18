"""工具：Excel 读写（G10）+ 杂项"""
from io import BytesIO
from typing import Any

from openpyxl import Workbook, load_workbook


def read_excel_sheet(file_bytes: bytes) -> tuple[list[str], list[dict[str, Any]]]:
    """读取第一个工作表。

    返回：(表头列表, 行数据列表)；每行以 {表头: 单元格值} 表示，
    自动跳过整行为空的数据行；行号通过 key="__row__" 附带（Excel 实际行号）。
    """
    try:
        wb = load_workbook(BytesIO(file_bytes), data_only=True, read_only=True)
    except Exception as exc:
        raise ValueError(f"Excel 文件解析失败，请上传有效的 .xlsx 文件：{exc}") from exc

    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        return [], []

    headers = [str(h).strip() if h is not None else "" for h in header_row]

    records: list[dict[str, Any]] = []
    for idx, raw in enumerate(rows_iter, start=2):
        values = list(raw)
        if all(v is None or str(v).strip() == "" for v in values):
            continue
        row: dict[str, Any] = {"__row__": idx}
        for i, h in enumerate(headers):
            row[h] = values[i] if i < len(values) else None
        records.append(row)
    wb.close()
    return headers, records


def write_excel_sheet(sheet_name: str, headers: list[str],
                      rows: list[list[Any]]) -> bytes:
    """生成 .xlsx 字节流（5.3 / 5.4 导出用）"""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buffer = BytesIO()
    wb.save(buffer)
    wb.close()
    return buffer.getvalue()
