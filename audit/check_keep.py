# -*- coding: utf-8 -*-
import openpyxl
from pathlib import Path

w = openpyxl.load_workbook(Path(r"D:\Develop\static-blog\audit\sresec-content-inventory-v3.xlsx"), read_only=True)
s = w["页面盘点"]
for row in s.iter_rows(min_row=2, values_only=True):
    seq, section, path, title, typ, chars, tmpl, ev, action, target, reason, priority, desc = row
    if section in ("操作指南", "速查手册") and action != "合并":
        print(f"{section}\t{action}\t{path}\t{title}\t{target}")
