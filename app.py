with open("app-v10.py", "r", encoding="utf-8") as f:
    src = f.read()

# Send PDF directly from in-memory BytesIO without leaving temporary files on disk or in BACKUP_DIR when streaming download,
# and clean up any old .tmp files in BACKUP_DIR or cwd.
old_gen = '''def generate_export_file(current_user, ts):'''
end_gen = '''@app.route("/", methods=["GET", "POST"])'''

s = src.find(old_gen)
e = src.find(end_gen)

new_gen = '''def _cleanup_tmp_files():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for folder in [base_dir, BACKUP_DIR]:
        try:
            for fn in os.listdir(folder):
                if fn.lower().endswith(".tmp"):
                    p = os.path.join(folder, fn)
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        except OSError:
            pass


def generate_export_file(current_user, ts):
    _cleanup_tmp_files()
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
    return filename, full_path, mimetype, content


'''

assert s != -1 and e != -1
updated = src[:s] + new_gen + src[e:]

# Update export_page POST to send directly from io.BytesIO(content) so no intermediate .tmp file is created during response
old_post = '''        export_file, full_path, mimetype = generate_export_file(current_user, ts)
        EXPORT_AUDITS.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": current_user,
            "type": "PDF",
            "backup": export_file
        })
        return send_file(full_path, mimetype=mimetype, as_attachment=True, download_name=export_file)'''

new_post = '''        export_file, full_path, mimetype, pdf_bytes = generate_export_file(current_user, ts)
        EXPORT_AUDITS.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": current_user,
            "type": "PDF",
            "backup": export_file
        })
        return send_file(io.BytesIO(pdf_bytes), mimetype=mimetype, as_attachment=True, download_name=export_file)'''

assert old_post in updated
updated = updated.replace(old_post, new_post, 1)

with open("app-v10.py", "w", encoding="utf-8") as f:
    f.write(updated)

with open("app-v10-clean.py", "w", encoding="utf-8") as f:
    f.write(updated)

print("Updated export to stream from memory and clean up .tmp files")
