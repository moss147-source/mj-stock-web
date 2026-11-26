# Let's make sure build_simple_pdf_bytes in app-v10.py also checks project-local fonts/windows fonts if deployed on Windows/Linux,
# and has crystal-clear Thai text rendering + watermark, and /export only supports PDF.
with open("app-v10.py", "r", encoding="utf-8") as f:
    src = f.read()

old_font_fn = '''def _find_thai_font_path():
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoLoopedThai-Regular.ttf",
        "/usr/share/fonts/truetype/thai/TlwgTypo.ttf",
        "/usr/share/fonts/truetype/thai/Loma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None'''

new_font_fn = '''def _find_thai_font_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "NotoSansThai-Regular.ttf"),
        os.path.join(base_dir, "fonts", "NotoSansThai-Regular.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoLoopedThai-Regular.ttf",
        "/usr/share/fonts/truetype/thai/TlwgTypo.ttf",
        "/usr/share/fonts/truetype/thai/Loma.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/angsa.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None'''

assert old_font_fn in src, "old_font_fn not found"
src = src.replace(old_font_fn, new_font_fn, 1)

with open("app-v10.py", "w", encoding="utf-8") as f:
    f.write(src)

print("Updated font search in app-v10.py")
