from pathlib import Path

ROOT = Path(r"D:\Develop\static-blog\docs\projects\homelab\practice")

for path in ROOT.glob("*.md"):
    text = path.read_text(encoding="utf-8")
    fixed = text.replace(
        "总表（含版本、地址、账号密码）",
        "总表（含版本、下载地址、账号规则）",
    )
    if fixed != text:
        path.write_text(fixed, encoding="utf-8", newline="\n")
        print(f"FIXED {path.name}")
