import os
import re

files_to_fix = [
    r"e:\whatsapp-business-platform\backend\app\modules\tenancy\service.py",
    r"e:\whatsapp-business-platform\backend\app\modules\contacts\service.py",
]

for file_path in files_to_fix:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    changed = False
    for i, line in enumerate(lines):
        if "__table__.insert(" in line or "__table__.update(" in line:
            if "# type: ignore[attr-defined]" not in line:
                lines[i] = line.rstrip() + "  # type: ignore[attr-defined]\n"
                changed = True
    
    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"Fixed {file_path}")
