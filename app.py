import os
import json
import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mj-stock-render-secret-key")
ADMIN_USER = os.environ.get("ADMIN_USER", "mj_admin")

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

PRODUCTS = {
    "8850001": {"code": "8850001", "name": "น้ำดื่มแพ็ค 12 ขวด", "price": 60, "qty": 24, "unit": "แพ็ค", "detail": "แพ็ค 12 ขวด ขนาด 600 มล."},
    "8850002": {"code": "8850002", "name": "กาแฟกระป๋อง", "price": 15, "qty": 48, "unit": "ชิ้น", "detail": "กระป๋อง 180 มล."},
    "8850003": {"code": "8850003", "name": "บะหมี่กึ่งสำเร็จรูป", "price": 7, "qty": 120, "unit": "ชิ้น", "detail": "รสหมูสับ ซอง 60 กรัม"}
}

STOCK_LOGS = []
EXPORT_AUDITS = []
REVIEWS = [
    {"user": "สมชาย", "stars": 5, "comment": "ใช้งานง่าย สแกนสินค้าแล้วข้อมูลขึ้นครบถ้วน"}
]

BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ระบบนับสต็อก ซอฟต์แวร์ โดย เอ็มเจ</title>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;600;700&display=swap" rel="stylesheet" />
  <style>
    * { box-sizing: border-box; font-family: 'Noto Sans Thai', sans-serif; }
    body { margin: 0; background: #f3f5f8; color: #1b2430; }
    header { background: #162232; color: #ffffff; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; }
    nav { background: #ffffff; border-bottom: 1px solid #d9e0e8; padding: 10px 24px; display: flex; gap: 10px; flex-wrap: wrap; }
    a.nav-btn, button { padding: 9px 14px; border: 1px solid #162232; border-radius: 6px; background: #162232; color: #ffffff; cursor: pointer; text-decoration: none; display: inline-block; font-size: 14px; }
    a.nav-btn.secondary, button.secondary { background: #ffffff; color: #162232; }
    main { max-width: 980px; margin: 24px auto; padding: 0 16px; }
    .card { background: #ffffff; border: 1px solid #d9e0e8; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
    input, select, textarea { width: 100%; padding: 9px 12px; margin: 6px 0 12px; border: 1px solid #bcc6d2; border-radius: 6px; }
    .msg-err { color: #a61b1b; margin-top: 8px; }
    .msg-ok { color: #155e36; margin-top: 8px; }
    .watermark-box { position: relative; border: 1px solid #bcc6d2; border-radius: 8px; padding: 28px; min-height: 220px; overflow: hidden; background: #ffffff; }
    .watermark-text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: 700; color: rgba(22, 34, 50, 0.15); transform: rotate(-22deg); pointer-events: none; user-select: none; text-align: center; }
    video { width: 100%; max-height: 280px; background: #162232; border-radius: 6px; margin-top: 8px; }
    footer { text-align: center; padding: 18px; color: #465465; font-size: 14px; }
    @media print {
      header, nav, .no-print, footer { display: none; }
      .watermark-text { color: rgba(22, 34, 50, 0.24); }
    }
  </style>
</head>
<body>
  <header>
    <div>ระบบนับสต็อก</div>
    <div>ซอฟต์แวร์ โดย เอ็มเจ</div>
  </header>

  {% if session.get("logged_in") %}
  <nav>
    <a class="nav-btn secondary" href="{{ url_for('stock') }}">นับสต็อก</a>
    <a class="nav-btn secondary" href="{{ url_for('pricing') }}">ราคาและจำนวน</a>
    <a class="nav-btn secondary" href="{{ url_for('export_page') }}">ส่งออก</a>
    <a class="nav-btn secondary" href="{{ url_for('review_page') }}">รีวิว</a>
    <a class="nav-btn secondary" href="{{ url_for('logout') }}">ออกจากระบบ</a>
  </nav>
  {% endif %}

  <main>
    {{ body_html | safe }}
  </main>

  <footer>ซอฟต์แวร์ โดย เอ็มเจ</footer>
</body>
</html>"""


SCANNER_BLOCK = """
<div style="border:1px solid #d9e0e8; border-radius:8px; padding:14px; margin-bottom:14px; background:#f8fafc;">
  <div>สแกนบาร์โค้ดและชื่อสินค้าอัตโนมัติด้วยกล้องและแฟลช</div>
  <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;">
    <button type="button" onclick="startCameraScan()">เปิดกล้องสแกนอัตโนมัติและขออนุญาต</button>
    <button type="button" class="secondary" onclick="toggleFlashlight()">เปิดหรือปิดแฟลช</button>
    <button type="button" class="secondary" onclick="stopCameraScan()">ปิดกล้อง</button>
  </div>
  <video id="scanVideo" playsinline autoplay muted style="display:none;"></video>
  <p id="cameraStatus" class="msg-ok"></p>
</div>
<script>
  let activeStream = null;
  let activeTrack = null;
  let torchOn = false;
  let scanTimer = null;
  let lastScannedCode = '';

  function fillScannedProduct(scanned) {
    const codeField = document.getElementById('codeInput') || document.getElementById('pricingCodeInput');
    const nameField = document.getElementById('nameInput') || document.getElementById('pricingNameInput');
    if (codeField) codeField.value = scanned;
    if (nameField && !nameField.value) nameField.value = 'สินค้า ' + scanned;
    if (typeof lookupBarcode === 'function') {
      lookupBarcode(scanned);
    }
  }

  async function startCameraScan() {
    const statusEl = document.getElementById('cameraStatus');
    const videoEl = document.getElementById('scanVideo');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, torch: true }
      });
      activeStream = stream;
      activeTrack = stream.getVideoTracks()[0];
      videoEl.srcObject = stream;
      videoEl.style.display = 'block';
      statusEl.textContent = 'อนุญาตใช้งานกล้องและแฟลชเรียบร้อยแล้ว กำลังสแกนบาร์โค้ดอัตโนมัติ';

      if (scanTimer) clearInterval(scanTimer);

      if ('BarcodeDetector' in window) {
        const detector = new BarcodeDetector({ formats: ['ean_13', 'ean_8', 'code_128', 'code_39', 'qr_code', 'upc_a', 'upc_e'] });
        scanTimer = setInterval(async () => {
          if (videoEl.readyState === 4) {
            try {
              const codes = await detector.detect(videoEl);
              if (codes.length > 0 && codes[0].rawValue) {
                const scanned = codes[0].rawValue.trim();
                if (scanned && scanned !== lastScannedCode) {
                  lastScannedCode = scanned;
                  fillScannedProduct(scanned);
                  statusEl.textContent = 'สแกนพบรหัสอัตโนมัติ: ' + scanned;
                }
              }
            } catch (e) {}
          }
        }, 450);
      } else {
        statusEl.textContent = 'เปิดกล้องแล้ว เบราว์เซอร์นี้ไม่รองรับ BarcodeDetector อัตโนมัติ สามารถกรอกหรือเลือกรหัสสินค้าได้ทันที';
      }
    } catch (err) {
      statusEl.textContent = 'ไม่สามารถเข้าถึงกล้องได้ กรุณาตรวจสอบการอนุญาตกล้องและแฟลชในเบราว์เซอร์';
    }
  }

  async function toggleFlashlight() {
    const statusEl = document.getElementById('cameraStatus');
    if (!activeTrack) {
      statusEl.textContent = 'กรุณาเปิดกล้องก่อนใช้งานแฟลช';
      return;
    }
    try {
      torchOn = !torchOn;
      await activeTrack.applyConstraints({ advanced: [{ torch: torchOn }] });
      statusEl.textContent = torchOn ? 'เปิดแฟลชแล้ว' : 'ปิดแฟลชแล้ว';
    } catch (err) {
      statusEl.textContent = 'อุปกรณ์หรือเบราว์เซอร์นี้ไม่รองรับการสั่งเปิดปิดแฟลชผ่านเว็บ';
    }
  }

  function stopCameraScan() {
    if (scanTimer) clearInterval(scanTimer);
    if (activeStream) {
      activeStream.getTracks().forEach(t => t.stop());
      activeStream = null;
      activeTrack = null;
    }
    const videoEl = document.getElementById('scanVideo');
    if (videoEl) {
      videoEl.srcObject = null;
      videoEl.style.display = 'none';
    }
    lastScannedCode = '';
    document.getElementById('cameraStatus').textContent = 'ปิดกล้องแล้ว';
  }
</script>
"""


def render_page(body_html):
    return render_template_string(BASE_TEMPLATE.replace("{{ body_html | safe }}", body_html))


def is_admin_user(username):
    return (username or "").strip() == ADMIN_USER


def can_access_audit(audit_item, current_user):
    if is_admin_user(current_user):
        return True
    return audit_item.get("user") == current_user


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    info = ""
    if request.method == "POST":
        action = request.form.get("action", "login")
        username = (request.form.get("username") or "").strip() or "ผู้ดูแลระบบ"
        recorder = (request.form.get("recorder") or "").strip() or username
        consent = request.form.get("consent")

        if not consent:
            error = "กรุณาติ๊กเลือกให้ความยินยอมผู้ใช้ก่อนเข้าใช้งานระบบ"
        elif action == "google":
            session["logged_in"] = True
            session["username"] = "บัญชีผู้ใช้กูเกิล"
            session["recorder"] = recorder
            return redirect(url_for("stock"))
        elif action == "register":
            info = "สร้างบัญชีใหม่เรียบร้อยแล้ว กรุณากดปุ่มเข้าสู่ระบบ"
        elif action == "forgot":
            info = "ส่งลิงก์รีเซ็ตรหัสผ่านเรียบร้อยแล้ว"
        else:
            session["logged_in"] = True
            session["username"] = username
            session["recorder"] = recorder
            return redirect(url_for("stock"))

    html = f"""
    <section class="card">
      <h2>เข้าสู่ระบบ</h2>
      <form method="post">
        <label>ชื่อผู้ใช้งาน</label>
        <input name="username" type="text" value="mj_admin" required />
        <label>ชื่อผู้บันทึกหรือผู้นับสต็อก</label>
        <input name="recorder" type="text" value="ผู้ดูแลระบบ" required />
        <label>รหัสผ่าน</label>
        <input name="password" type="password" value="123456" required />
        <label>
          <input name="consent" type="checkbox" style="width:auto; margin-right:8px;" />
          ฉันยอมรับเงื่อนไขและให้ความยินยอมในการเข้าถึงข้อมูลเพื่อใช้งานระบบ
        </label>
        <div style="display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;">
          <button type="submit" name="action" value="login">เข้าสู่ระบบ</button>
          <button type="submit" name="action" value="register" class="secondary">สร้างบัญชี</button>
          <button type="submit" name="action" value="forgot" class="secondary">ลืมรหัสผ่าน</button>
          <button type="submit" name="action" value="google" class="secondary">สร้างบัญชีด้วยกูเกิล</button>
        </div>
      </form>
      <p class="msg-err">{error}</p>
      <p class="msg-ok">{info}</p>
    </section>
    """
    return render_page(html)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/product/<code>")
def get_product(code):
    item = PRODUCTS.get(code)
    if not item:
        return jsonify({"found": False}), 404
    return jsonify({"found": True, "product": item})


@app.route("/stock", methods=["GET", "POST"])
def stock():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    status_msg = ""
    if request.method == "POST":
        code = (request.form.get("code") or "").strip()
        name = (request.form.get("name") or "").strip()
        price = request.form.get("price") or "0"
        qty = request.form.get("qty") or "0"
        unit = request.form.get("unit") or "ชิ้น"
        record = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": session.get("username", "ผู้ดูแลระบบ"),
            "recorder": session.get("recorder", "ผู้ดูแลระบบ"),
            "code": code,
            "name": name,
            "price": price,
            "qty": qty,
            "unit": unit
        }
        STOCK_LOGS.append(record)
        status_msg = f"บันทึกการนับสต็อก {name} จำนวน {qty} {unit} เรียบร้อยแล้ว ใช้สำหรับบันทึกการนับเท่านั้น ไม่ปรับข้อมูลสต็อกหลัก"

    options_html = "".join(
        [f'<option value="{c}">{c} - {p["name"]}</option>' for c, p in PRODUCTS.items()]
    )
    logs_html = "".join(
        [f'<li>{r["time"]} | ผู้ใช้ {r["user"]} | ผู้นับสต็อก {r["recorder"]} | รหัส {r["code"]} | {r["name"]} | ราคา {r["price"]} | จำนวน {r["qty"]} {r["unit"]}</li>' for r in reversed(STOCK_LOGS)]
    )

    html = f"""
    <section class="card">
      <h2>นับสต็อก</h2>
      <p>ชื่อผู้ใช้งาน: <strong>{session.get("username", "-")}</strong> | ชื่อผู้บันทึกหรือผู้นับสต็อก: <strong>{session.get("recorder", "-")}</strong></p>
      <p>ใช้สำหรับกรอกข้อมูลเพื่อบันทึกการนับสต็อกเท่านั้น ไม่สามารถใช้ปรับข้อมูลสต็อกหลักได้</p>
      {SCANNER_BLOCK}
      <form method="post" id="stockForm">
        <label>สแกนหรือเลือกรหัสสินค้า บาร์โค้ด</label>
        <select id="barcodePicker" onchange="lookupBarcode(this.value)">
          <option value="">เลือกรหัสสินค้าเพื่อสแกน</option>
          {options_html}
        </select>
        <label>รหัสสินค้า บาร์โค้ด</label>
        <input id="codeInput" name="code" type="text" required onchange="lookupBarcode(this.value)" />
        <label>ชื่อสินค้า</label>
        <input id="nameInput" name="name" type="text" required />
        <label>ราคาต่อหน่วย</label>
        <input id="priceInput" name="price" type="number" step="any" required />
        <label>จำนวนสินค้า ต่อชิ้นหรือแพ็ค</label>
        <input id="qtyInput" name="qty" type="number" step="any" required />
        <label>หน่วย</label>
        <select id="unitInput" name="unit">
          <option value="ชิ้น">ชิ้น</option>
          <option value="แพ็ค">แพ็ค</option>
          <option value="กล่อง">กล่อง</option>
          <option value="ขวด">ขวด</option>
          <option value="ลัง">ลัง</option>
        </select>
        <button type="submit">บันทึกการนับสต็อก</button>
      </form>
      <p class="msg-ok">{status_msg}</p>
      <h3>รายการนับสต็อกที่บันทึกแล้ว</h3>
      <ul>{logs_html}</ul>
    </section>
    <script>
      async function lookupBarcode(code) {{
        if (!code) return;
        const res = await fetch('/api/product/' + encodeURIComponent(code.trim()));
        if (!res.ok) return;
        const data = await res.json();
        if (data.found) {{
          document.getElementById('codeInput').value = data.product.code;
          document.getElementById('nameInput').value = data.product.name;
          document.getElementById('priceInput').value = data.product.price;
          document.getElementById('qtyInput').value = data.product.qty;
          document.getElementById('unitInput').value = data.product.unit || 'ชิ้น';
        }}
      }}
    </script>
    """
    return render_page(html)


@app.route("/pricing", methods=["GET", "POST"])
def pricing():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action", "add")
        code = (request.form.get("code") or "").strip()
        if action == "delete" and code in PRODUCTS:
            del PRODUCTS[code]
        elif action == "add" and code:
            PRODUCTS[code] = {
                "code": code,
                "name": (request.form.get("name") or "").strip(),
                "price": float(request.form.get("price") or 0),
                "qty": int(float(request.form.get("qty") or 0)),
                "unit": request.form.get("unit") or "ชิ้น",
                "detail": (request.form.get("detail") or "").strip()
            }

    rows_html = ""
    for c, p in PRODUCTS.items():
        rows_html += f"""
        <div style="padding:10px 0; border-bottom:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
          <div>รหัส {p["code"]} | ชื่อ {p["name"]} | ราคา {p["price"]} บาท | จำนวน {p["qty"]} {p["unit"]} | รายละเอียด {p["detail"]}</div>
          <form method="post" style="margin:0;">
            <input type="hidden" name="action" value="delete" />
            <input type="hidden" name="code" value="{p["code"]}" />
            <button type="submit" class="secondary">ลบสินค้า</button>
          </form>
        </div>
        """

    html = f"""
    <section class="card">
      <h2>ราคาและจำนวน</h2>
      {SCANNER_BLOCK}
      <form method="post">
        <input type="hidden" name="action" value="add" />
        <label>ชื่อสินค้า</label>
        <input id="pricingNameInput" name="name" type="text" required />
        <label>รหัสสินค้า</label>
        <input id="pricingCodeInput" name="code" type="text" required />
        <label>ราคา</label>
        <input id="pricingPriceInput" name="price" type="number" step="any" required />
        <label>จำนวน</label>
        <input id="pricingQtyInput" name="qty" type="number" step="any" required />
        <label>หน่วย</label>
        <select id="pricingUnitInput" name="unit">
          <option value="ชิ้น">ชิ้น</option>
          <option value="แพ็ค">แพ็ค</option>
          <option value="กล่อง">กล่อง</option>
          <option value="ขวด">ขวด</option>
          <option value="ลัง">ลัง</option>
        </select>
        <label>รายละเอียดสินค้า</label>
        <textarea name="detail" rows="2"></textarea>
        <button type="submit">เพิ่มสินค้า</button>
      </form>
      <div style="margin-top:16px;">{rows_html}</div>
    </section>
    <script>
      async function lookupBarcode(code) {{
        if (!code) return;
        const res = await fetch('/api/product/' + encodeURIComponent(code.trim()));
        if (!res.ok) return;
        const data = await res.json();
        if (data.found) {{
          document.getElementById('pricingCodeInput').value = data.product.code;
          document.getElementById('pricingNameInput').value = data.product.name;
          document.getElementById('pricingPriceInput').value = data.product.price;
          document.getElementById('pricingQtyInput').value = data.product.qty;
          document.getElementById('pricingUnitInput').value = data.product.unit || 'ชิ้น';
        }}
      }}
    </script>
    """
    return render_page(html)


@app.route("/export", methods=["GET", "POST"])
def export_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    current_user = session.get("username", "ผู้ดูแลระบบ")
    err_msg = ""
    if request.method == "POST":
        export_type = request.form.get("export_type", "PDF")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{current_user}_{export_type}_{ts}.json"
        payload = {
            "watermark": "ระบบนับสต็อก พัฒนาโดย เอ็มเจ",
            "exported_by": current_user,
            "export_type": export_type,
            "exported_at": ts,
            "products": list(PRODUCTS.values()),
            "stock_logs": STOCK_LOGS
        }
        with open(os.path.join(BACKUP_DIR, backup_file), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        EXPORT_AUDITS.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": current_user,
            "type": export_type,
            "backup": backup_file
        })

    visible_audits = [a for a in EXPORT_AUDITS if can_access_audit(a, current_user)]
    audit_html = "".join(
        [f'<li>{a["time"]} | ผู้ใช้ {a["user"]} | ประเภท {a["type"]} | ไฟล์สำรอง <a href="/backups/{a["backup"]}">{a["backup"]}</a></li>' for a in reversed(visible_audits)]
    )
    scope_text = "ผู้ดูแลระบบ: เข้าถึงไฟล์สำรองของทุกคนได้" if is_admin_user(current_user) else f"ผู้ใช้ {current_user}: เข้าถึงได้เฉพาะไฟล์สำรองของตัวเอง"

    html = f"""
    <section class="card">
      <h2>ส่งออกและประวัติผู้ดูแลระบบ</h2>
      <p>{scope_text}</p>
      <form method="post" class="no-print" style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:14px;">
        <button type="submit" name="export_type" value="PDF">ส่งออก PDF</button>
        <button type="submit" name="export_type" value="Word">ส่งออก Word</button>
        <button type="submit" name="export_type" value="Excel">ส่งออก Excel</button>
        <button type="submit" name="export_type" value="Print" onclick="setTimeout(()=>window.print(), 100)">พิมพ์</button>
      </form>
      <div class="watermark-box">
        <div class="watermark-text">ระบบนับสต็อก พัฒนาโดย เอ็มเจ</div>
        <div>เนื้อหารายงานสต็อกและสำรองข้อมูลของระบบ</div>
      </div>
      <p class="msg-err">{err_msg}</p>
      <h3 style="margin-top:18px;">ประวัติการส่งออกและพิมพ์</h3>
      <ul>{audit_html}</ul>
    </section>
    """
    return render_page(html)


@app.route("/backups/<filename>")
def download_backup(filename):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    current_user = session.get("username", "ผู้ดูแลระบบ")
    matched = next((a for a in EXPORT_AUDITS if a.get("backup") == filename), None)
    if matched and not can_access_audit(matched, current_user):
        return "ไม่มีสิทธิ์เข้าถึงไฟล์สำรองของผู้ใช้อื่น", 403
    if not is_admin_user(current_user) and not filename.startswith(f"backup_{current_user}_"):
        return "ไม่มีสิทธิ์เข้าถึงไฟล์สำรองของผู้ใช้อื่น", 403
    return send_from_directory(BACKUP_DIR, filename, as_attachment=True)


@app.route("/review", methods=["GET", "POST"])
def review_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    share_msg = ""
    if request.method == "POST":
        action = request.form.get("action", "submit")
        if action == "share":
            share_msg = "คัดลอกข้อความประชาสัมพันธ์ระบบนับสต็อก ซอฟต์แวร์ โดย เอ็มเจ สำหรับแชร์ไปยังช่องทางอื่นแล้ว"
        else:
            stars = int(request.form.get("stars") or 5)
            comment = (request.form.get("comment") or "").strip()
            if comment:
                REVIEWS.append({
                    "user": session.get("username", "ผู้ดูแลระบบ"),
                    "stars": stars,
                    "comment": comment
                })

    reviews_html = "".join(
        [f'<li>คะแนน {r["stars"]} ดาว โดย {r["user"]}: {r["comment"]}</li>' for r in reversed(REVIEWS)]
    )

    html = f"""
    <section class="card">
      <h2>รีวิว</h2>
      <form method="post">
        <label>ให้คะแนน 1 ถึง 5 ดาว</label>
        <select name="stars">
          <option value="5">5 ดาว</option>
          <option value="4">4 ดาว</option>
          <option value="3">3 ดาว</option>
          <option value="2">2 ดาว</option>
          <option value="1">1 ดาว</option>
        </select>
        <label>ข้อความรีวิว</label>
        <textarea name="comment" rows="3" placeholder="เขียนรีวิวการใช้งานระบบ"></textarea>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <button type="submit" name="action" value="submit">ส่งรีวิว</button>
          <button type="submit" name="action" value="share" class="secondary">แชร์ไปยังช่องทางอื่น</button>
        </div>
      </form>
      <p class="msg-ok">{share_msg}</p>
      <ul style="margin-top:14px;">{reviews_html}</ul>
    </section>
    """
    return render_page(html)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
