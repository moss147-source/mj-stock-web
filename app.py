with open("app-v10.py", "r", encoding="utf-8") as f:
    src = f.read()

# Check if any old English report strings or multiple export buttons remain in app-v10.py
for kw in ["MJ Stock Report", "Exported By:", "ส่งออก Word", "ส่งออก Excel", "พิมพ์"]:
    print(kw, "->", kw in src)

# Also let's check if we should make sure Dockerfile/render deployment or app-v10.py also downloads/bundles NotoSansThai if missing at runtime,
# or generates a crisp PDF with ReportLab/fpdf2/PIL + NotoSansThai. Let's check what python packages are in app-v10.py.
print("\nImports in app-v10.py:")
for line in src.splitlines()[:15]:
    print(line)
