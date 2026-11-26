def _find_thai_font_path():
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
        "/tmp/NotoSansThai-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.getsize(p) > 20000:
            return p

    try:
        import urllib.request
        url = "https://github.com/google/fonts/raw/main/ofl/notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf"
        target = "/tmp/NotoSansThai-Regular.ttf"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        if len(data) > 20000:
            with open(target, "wb") as out:
                out.write(data)
            return target
    except Exception:
        pass

    return None


def generate_export_file(current_user, ts):
    lines = [
        "ลายน้ำ ระบบนับสต็อก Developed by MJ",
        "รายงานการนับสต็อก ระบบนับสต็อก Developed by MJ",
        f"ผู้ส่งออก {current_user}",
        f"วันเวลาที่ส่งออก {ts}",
        "รายการสินค้าทั้งหมด",
    ]
    for p in PRODUCTS.values():
        lines.append(
            f"รหัส {p['code']} ชื่อสินค้า {p['name']} ราคา {p['price']} บาท จำนวน {p['qty']} {p['unit']} รายละเอียด {p['detail']}"
        )
    lines.append("รายละเอียดการนับสต็อก")
    for r in STOCK_LOGS:
        lines.append(
            f"เวลา {r['time']} ผู้ใช้ {r['user']} ผู้นับสต็อก {r['recorder']} รหัส {r['code']} ชื่อสินค้า {r['name']} ราคา {r['price']} บาท จำนวน {r['qty']} {r['unit']}"
        )

    filename = f"report_{current_user}_{ts}.pdf"
    content = build_simple_pdf_bytes(lines, watermark_text="ระบบนับสต็อก Developed by MJ")
    mimetype = "application/pdf"

    full_path = os.path.join(BACKUP_DIR, filename)
    with open(full_path, "wb") as f:
        f.write(content)
    return filename, full_path, mimetype
