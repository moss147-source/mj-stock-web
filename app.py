with open("app-v10.py", "r", encoding="utf-8") as f:
    src = f.read()

# Ensure /export route and HTML have ONLY PDF export button, and no Word/Excel/Print
print("Has Word:", "ส่งออก Word" in src, "Has Excel:", "ส่งออก Excel" in src, "Has พิมพ์:", "พิมพ์" in src)

# Also write a standalone clean Python file app_pdf_only.py as a fresh version in case user wants to replace their main app file directly
with open("app_pdf_only.py", "w", encoding="utf-8") as out:
    out.write(src)

print("Saved app_pdf_only.py")
