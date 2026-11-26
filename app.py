def generate_export_file(current_user, ts):
    lines = [
        "ลายน้ำ ระบบนับสต็อก พัฒนาโดย เอ็มเจ",
        "รายงานการนับสต็อก ระบบนับสต็อก พัฒนาโดย เอ็มเจ",
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
    content = build_simple_pdf_bytes(lines, watermark_text="ระบบนับสต็อก พัฒนาโดย เอ็มเจ")
    mimetype = "application/pdf"

    full_path = os.path.join(BACKUP_DIR, filename)
    with open(full_path, "wb") as f:
        f.write(content)
    return filename, full_path, mimetype


@app.route("/export", methods=["GET", "POST"])
def export_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    current_user = session.get("username", "ผู้ดูแลระบบ")

    if request.method == "POST":
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file, full_path, mimetype = generate_export_file(current_user, ts)
        EXPORT_AUDITS.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": current_user,
            "type": "PDF",
            "backup": export_file
        })
        return send_file(full_path, mimetype=mimetype, as_attachment=True, download_name=export_file)

    visible_audits = [a for a in EXPORT_AUDITS if can_access_audit(a, current_user)]
    audit_html = "".join(
        [f'<li>{a["time"]} | ผู้ใช้ {a["user"]} | ประเภท {a["type"]} | ไฟล์ส่งออก <a href="/backups/{a["backup"]}">{a["backup"]}</a></li>' for a in reversed(visible_audits)]
    )
    scope_text = "ผู้ดูแลระบบ เข้าถึงไฟล์สำรองของทุกคนได้" if is_admin_user(current_user) else f"ผู้ใช้ {current_user} เข้าถึงได้เฉพาะไฟล์สำรองของตัวเอง"

    prod_rows_html = "".join(
        [f"<tr><td>{p['code']}</td><td>{p['name']}</td><td>{p['price']}</td><td>{p['qty']}</td><td>{p['unit']}</td><td>{p['detail']}</td></tr>" for p in PRODUCTS.values()]
    )
    log_rows_html = "".join(
        [f"<tr><td>{r['time']}</td><td>{r['user']}</td><td>{r['recorder']}</td><td>{r['code']}</td><td>{r['name']}</td><td>{r['price']}</td><td>{r['qty']} {r['unit']}</td></tr>" for r in reversed(STOCK_LOGS)]
    )

    html = f"""
    <section class="card">
      <h2>ส่งออกและประวัติผู้ดูแลระบบ</h2>
      <p>{scope_text}</p>
      <form method="post" class="no-print" style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px;">
        <button type="submit" name="export_type" value="PDF">ส่งออก PDF</button>
      </form>
      <div class="watermark-box">
        <div class="watermark-text">ระบบนับสต็อก พัฒนาโดย เอ็มเจ</div>
        <div>เนื้อหารายงานสต็อกและสำรองข้อมูลของระบบ</div>
        <table>
          <thead>
            <tr><th>รหัส</th><th>ชื่อสินค้า</th><th>ราคา</th><th>จำนวน</th><th>หน่วย</th><th>รายละเอียด</th></tr>
          </thead>
          <tbody>{prod_rows_html}</tbody>
        </table>
        <h4 style="margin-top:14px;">รายละเอียดการนับสต็อก</h4>
        <table>
          <thead>
            <tr><th>เวลา</th><th>ผู้ใช้</th><th>ผู้นับสต็อก</th><th>รหัส</th><th>ชื่อสินค้า</th><th>ราคา</th><th>จำนวน</th></tr>
          </thead>
          <tbody>{log_rows_html}</tbody>
        </table>
      </div>
      <h3 class="no-print" style="margin-top:18px;">ประวัติการส่งออก</h3>
      <ul class="no-print">{audit_html}</ul>
    </section>
    """
    return render_page(html)
