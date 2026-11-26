import os
import io
import csv
import datetime
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template_string, request, redirect, url_for, session, send_from_directory, send_file, jsonify

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
REVIEWS = []

BASE_TEMPLATE = """<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ระบบนับสต็อก โดย เอ็มเจ</title>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    * { box-sizing: border-box; font-family: 'Noto Sans Thai', sans-serif; }
    body { margin: 0; background: #f3f5f9; color: #162232; }
    .utility-bar { background: #0f172a; color: #cbd5e1; font-size: 13px; padding: 8px 24px; }
    .utility-inner { max-width: 1160px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
    .navbar { background: #ffffff; border-bottom: 1px solid #e2e8f0; box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05); position: sticky; top: 0; z-index: 50; }
    .nav-inner { max-width: 1160px; margin: 0 auto; padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; }
    .brand { display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 700; color: #0f172a; text-decoration: none; }
    .brand-badge { background: #dc2626; color: #ffffff; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 700; }
    .nav-menu { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .nav-item { position: relative; }
    a.nav-btn, button { padding: 8px 14px; border: 1px solid #cbd5e1; border-radius: 6px; background: #ffffff; color: #162232; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; justify-content: center; gap: 6px; font-size: 14px; font-weight: 600; transition: all 0.15s ease; }
    a.nav-btn:hover, button:hover { background: #0f172a; color: #ffffff; border-color: #0f172a; }
    a.nav-btn.primary, button.primary { background: #0f172a; color: #ffffff; border-color: #0f172a; }
    a.nav-btn.primary:hover, button.primary:hover { background: #1e293b; }
    a.nav-btn.secondary, button.secondary { background: #ffffff; color: #162232; border-color: #cbd5e1; }
    .dropdown-panel { display: none; position: absolute; top: calc(100% + 6px); left: 0; min-width: 210px; background: #dc2626; border-radius: 8px; box-shadow: 0 12px 24px rgba(15, 23, 42, 0.18); padding: 6px 0; z-index: 60; }
    .nav-item:hover .dropdown-panel { display: block; }
    .dropdown-link { display: block; width: 100%; text-align: left; background: transparent; border: none; color: #ffffff; padding: 10px 16px; font-size: 14px; font-weight: 500; text-decoration: none; }
    .dropdown-link:hover { background: rgba(255, 255, 255, 0.14); color: #ffffff; }
    .user-box { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; padding: 6px 12px; border-radius: 999px; font-size: 13px; font-weight: 600; }
    main { max-width: 1120px; margin: 24px auto; padding: 0 20px; }
    .card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 22px; margin-bottom: 18px; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03); }
    h2 { margin-top: 0; color: #0f172a; font-size: 20px; }
    label { display: block; font-size: 13px; font-weight: 600; color: #334155; }
    input, select, textarea { width: 100%; padding: 9px 12px; margin: 4px 0 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; background: #ffffff; }
    .form-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .form-grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
    .scanner-box { border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px; margin-bottom: 12px; background: #f8fafc; }
    .scanner-header { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #0f172a; }
    .scanner-actions { display: grid; grid-template-columns: 1.4fr 1fr 0.85fr; gap: 8px; margin-top: 10px; }
    .btn-cam, .btn-flash, .btn-stop { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 9px 10px; border-radius: 9px; font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap; transition: all 0.15s ease; }
    .btn-cam { background: #0f172a; color: #ffffff; border: 1px solid #0f172a; }
    .btn-cam:hover { background: #1e293b; color: #ffffff; }
    .btn-flash { background: #fffbeb; color: #b45309; border: 1px solid #f59e0b; }
    .btn-flash:hover, .btn-flash.active { background: #f59e0b; color: #ffffff; }
    .btn-stop { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
    .btn-stop:hover { background: #dc2626; color: #ffffff; }
    .btn-icon { width: 15px; height: 15px; flex-shrink: 0; }
    .msg-err { color: #b91c1c; margin: 6px 0 0; font-weight: 600; font-size: 13px; }
    .msg-ok { color: #15803d; margin: 6px 0 0; font-weight: 600; font-size: 13px; }
    .watermark-box { position: relative; border: 1px solid #cbd5e1; border-radius: 8px; padding: 28px; min-height: 220px; overflow: hidden; background: #ffffff; }
    .watermark-text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 36px; font-weight: 700; color: rgba(22, 34, 50, 0.14); transform: rotate(-22deg); pointer-events: none; user-select: none; text-align: center; }
    video { width: 100%; max-height: 180px; background: #162232; border-radius: 6px; margin-top: 6px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { border: 1px solid #e2e8f0; padding: 7px 8px; text-align: left; font-size: 13px; }
    th { background: #f8fafc; color: #0f172a; }
    footer { text-align: center; padding: 12px; color: #64748b; font-size: 12px; }

    @media (max-width: 640px) {
      .utility-bar { padding: 3px 8px; font-size: 10px; }
      .utility-inner { gap: 4px; }
      .nav-inner { padding: 5px 8px; gap: 4px; }
      .brand { font-size: 14px; gap: 5px; }
      .brand-badge { padding: 2px 5px; font-size: 10px; }
      .user-box { padding: 2px 7px; font-size: 10px; }
      .nav-menu { width: 100%; display: grid; grid-template-columns: repeat(5, 1fr); gap: 3px; }
      .nav-item { width: 100%; }
      .nav-menu a.nav-btn { width: 100%; padding: 5px 2px; font-size: 10.5px; text-align: center; white-space: nowrap; }
      .dropdown-panel { display: none !important; }
      main { margin: 5px auto; padding: 0 6px; }
      .card { padding: 9px; margin-bottom: 6px; border-radius: 8px; }
      h2 { font-size: 15px; margin-bottom: 4px; }
      h3 { font-size: 13px; margin: 6px 0 3px; }
      h4 { font-size: 12px; margin: 6px 0 3px; }
      p { margin: 2px 0 5px; font-size: 11.5px; line-height: 1.3; }
      .hint-mobile-hide { display: none; }
      .scanner-box { padding: 7px; margin-bottom: 6px; }
      .scanner-header { font-size: 11.5px; }
      .scanner-actions { display: grid; grid-template-columns: 1.4fr 1fr 0.85fr; gap: 4px; margin-top: 5px; }
      .scanner-actions button { padding: 7px 4px; font-size: 11px; white-space: nowrap; border-radius: 8px; }
      .btn-icon { width: 13px; height: 13px; }
      label { font-size: 11px; margin-bottom: 1px; }
      input, select, textarea { padding: 5px 7px; margin: 2px 0 5px; font-size: 12.5px; }
      .form-grid-2 { grid-template-columns: 1fr 1fr; gap: 5px; }
      .form-grid-3 { grid-template-columns: 1fr 1fr 1fr; gap: 5px; }
      button[type="submit"], button.secondary { padding: 7px 8px; font-size: 12px; }
      form[method="post"] > button[type="submit"] { width: 100%; }
      .watermark-box { padding: 10px; min-height: 120px; }
      .watermark-text { font-size: 20px; }
      table { margin-top: 6px; display: block; overflow-x: auto; }
      th, td { padding: 5px 6px; font-size: 11px; white-space: nowrap; }
      ul { padding-left: 15px; margin: 3px 0; font-size: 11px; max-height: 75px; overflow-y: auto; }
      footer { padding: 5px; font-size: 10.5px; }
    }
    @media print {
      .utility-bar, .navbar, .no-print, footer { display: none; }
      .watermark-text { color: rgba(22, 34, 50, 0.24); }
    }
  </style>
</head>
<body>
  <div class="utility-bar">
    <div class="utility-inner">
      <div>ระบบนับสต็อกและรายงานข้อมูลสินค้า</div>
      <div>27 พฤศจิกายน พ.ศ. 2569 05:11 น.</div>
    </div>
  </div>

  <header class="navbar">
    <div class="nav-inner">
      <a class="brand" href="{{ url_for('stock') if session.get('logged_in') else url_for('login') }}">
        <span class="brand-badge">MJ</span>
        <span>ระบบนับสต็อก</span>
      </a>

      {% if session.get("logged_in") %}
      <nav class="nav-menu">
        <a class="nav-btn secondary" href="{{ url_for('stock') }}">นับสต็อก</a>
        <div class="nav-item">
          <a class="nav-btn secondary" href="{{ url_for('pricing') }}">ราคาและจำนวน</a>
          <div class="dropdown-panel">
            <a class="dropdown-link" href="{{ url_for('pricing') }}">รายการสินค้าและราคา</a>
            <a class="dropdown-link" href="{{ url_for('stock') }}">บันทึกรับนับสินค้า</a>
          </div>
        </div>
        <a class="nav-btn secondary" href="{{ url_for('export_page') }}">ส่งออก</a>
        <a class="nav-btn secondary" href="{{ url_for('review_page') }}">รีวิว</a>
        <a class="nav-btn secondary" href="{{ url_for('logout') }}">ออกจากระบบ</a>
        <span class="user-box">{{ session.get("username") }}</span>
      </nav>
      {% else %}
      <div class="user-box">ซอฟต์แวร์ โดย เอ็มเจ</div>
      {% endif %}
    </div>
  </header>

  <main>
    {{ body_html | safe }}
  </main>

  <footer>ซอฟต์แวร์ โดย เอ็มเจ</footer>
</body>
</html>"""

SCANNER_BLOCK = """
<div class="scanner-box">
  <div class="scanner-header">
    <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M3 7V5a2 2 0 0 1 2-2h2"/>
      <path d="M17 3h2a2 2 0 0 1 2 2v2"/>
      <path d="M21 17v2a2 2 0 0 1-2 2h-2"/>
      <path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
      <line x1="7" y1="12" x2="17" y2="12"/>
    </svg>
    <span>สแกนบาร์โค้ดและชื่อสินค้าอัตโนมัติ</span>
  </div>
  <div class="scanner-actions">
    <button type="button" class="btn-cam" onclick="startCameraScan()">
      <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
        <circle cx="12" cy="13" r="3"/>
      </svg>
      <span>เปิดกล้องสแกน</span>
    </button>
    <button type="button" id="flashBtn" class="btn-flash" onclick="toggleFlashlight()">
      <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
      </svg>
      <span id="flashBtnText">เปิดแฟลช</span>
    </button>
    <button type="button" class="btn-stop" onclick="stopCameraScan()">
      <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
      <span>ปิดกล้อง</span>
    </button>
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
      const flashBtn = document.getElementById('flashBtn');
      const flashText = document.getElementById('flashBtnText');
      if (flashBtn) flashBtn.classList.toggle('active', torchOn);
      if (flashText) flashText.textContent = torchOn ? 'ปิดแฟลช' : 'เปิดแฟลช';
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
    torchOn = false;
    const flashBtn = document.getElementById('flashBtn');
    const flashText = document.getElementById('flashBtnText');
    if (flashBtn) flashBtn.classList.remove('active');
    if (flashText) flashText.textContent = 'เปิดแฟลช';
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


def build_simple_pdf_bytes(lines, watermark_text="ระบบนับสต็อก Developed by MJ"):
    page_w, page_h = 1240, 1754
    margin_x, margin_y = 70, 75
    line_h = 34
    max_lines_per_page = max(1, (page_h - margin_y * 2) // line_h)

    font_path = _find_thai_font_path()
    if font_path:
        body_font = ImageFont.truetype(font_path, 22)
        wm_font = ImageFont.truetype(font_path, 52)
    else:
        body_font = ImageFont.load_default()
        wm_font = ImageFont.load_default()

    dummy_img = Image.new("RGB", (page_w, page_h), "white")
    dummy_draw = ImageDraw.Draw(dummy_img)
    max_text_w = page_w - margin_x * 2

    wrapped = []
    for line in lines:
        s = str(line)
        if not s:
            wrapped.append("")
            continue
        cur = ""
        for ch in s:
            test = cur + ch
            bbox = dummy_draw.textbbox((0, 0), test, font=body_font)
            if (bbox[2] - bbox[0]) <= max_text_w:
                cur = test
            else:
                wrapped.append(cur)
                cur = ch
        if cur:
            wrapped.append(cur)

    pages_lines = [wrapped[i:i + max_lines_per_page] for i in range(0, max(1, len(wrapped)), max_lines_per_page)]
    jpeg_pages = []

    for p_lines in pages_lines:
        img = Image.new("RGB", (page_w, page_h), (255, 255, 255))
        draw = ImageDraw.Draw(img, "RGBA")

        y = margin_y
        for ln in p_lines:
            draw.text((margin_x, y), ln, fill=(27, 36, 48, 255), font=body_font)
            y += line_h

        wm_layer = Image.new("RGBA", (page_w, page_h), (255, 255, 255, 0))
        wm_draw = ImageDraw.Draw(wm_layer, "RGBA")
        wm_bbox = wm_draw.textbbox((0, 0), watermark_text, font=wm_font)
        tw, th = max(1, wm_bbox[2] - wm_bbox[0]), max(1, wm_bbox[3] - wm_bbox[1])
        wm_patch = Image.new("RGBA", (tw + 40, th + 40), (255, 255, 255, 0))
        ImageDraw.Draw(wm_patch, "RGBA").text((20, 20), watermark_text, fill=(22, 34, 50, 38), font=wm_font)
        rotated = wm_patch.rotate(28, expand=True, resample=Image.BICUBIC)
        rw, rh = rotated.size
        for gx in range(-100, page_w + rw, rw + 140):
            for gy in range(-100, page_h + rh, rh + 180):
                wm_layer.alpha_composite(rotated, (gx, gy))

        img = Image.alpha_composite(img.convert("RGBA"), wm_layer).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=88)
        jpeg_pages.append(buf.getvalue())

    objs = []
    page_obj_ids = []
    next_id = 3
    page_specs = []
    for jpg in jpeg_pages:
        page_id = next_id
        img_id = next_id + 1
        cnt_id = next_id + 2
        next_id += 3
        page_obj_ids.append(page_id)
        page_specs.append((page_id, img_id, cnt_id, jpg))

    objs.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objs.append(f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {len(page_obj_ids)} >>\nendobj\n".encode("ascii"))

    for page_id, img_id, cnt_id, jpg in page_specs:
        content_stream = b"q\n595 0 0 842 0 0 cm\n/Im1 Do\nQ\n"
        objs.append(
            f"{page_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /XObject << /Im1 {img_id} 0 R >> >> /Contents {cnt_id} 0 R >>\nendobj\n".encode("ascii")
        )
        objs.append(
            f"{img_id} 0 obj\n<< /Type /XObject /Subtype /Image /Width {page_w} /Height {page_h} "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(jpg)} >>\nstream\n".encode("ascii")
            + jpg
            + b"\nendstream\nendobj\n"
        )
        objs.append(
            f"{cnt_id} 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode("ascii")
            + content_stream
            + b"\nendstream\nendobj\n"
        )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objs:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


def _cleanup_tmp_files():
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


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    info = ""
    if request.method == "POST":
        action = request.form.get("action", "login")
        username = (request.form.get("username") or "").strip() or "ผู้ใช้งาน"
        consent = request.form.get("consent")

        if not consent:
            error = "กรุณาติ๊กเลือกให้ความยินยอมผู้ใช้ก่อนเข้าใช้งานระบบ"
        elif action == "google":
            session["logged_in"] = True
            session["username"] = "บัญชีผู้ใช้กูเกิล"
            session["recorder"] = ""
            return redirect(url_for("stock"))
        elif action == "register":
            info = "สร้างบัญชีใหม่เรียบร้อยแล้ว กรุณากดปุ่มเข้าสู่ระบบ"
        elif action == "forgot":
            info = "ส่งลิงก์รีเซ็ตรหัสผ่านเรียบร้อยแล้ว"
        else:
            session["logged_in"] = True
            session["username"] = username
            session["recorder"] = ""
            return redirect(url_for("stock"))

    html = f"""
    <section class="card">
      <h2>เข้าสู่ระบบ</h2>
      <form method="post" autocomplete="off">
        <label>ชื่อผู้ใช้งาน</label>
        <input name="username" type="text" value="" autocomplete="off" />
        <label>รหัสผ่าน</label>
        <input name="password" type="password" value="" autocomplete="new-password" />
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
        recorder_input = (request.form.get("recorder") or "").strip()
        if recorder_input:
            session["recorder"] = recorder_input
        recorder = session.get("recorder") or session.get("username", "ผู้ใช้งาน")

        code = (request.form.get("code") or "").strip()
        name = (request.form.get("name") or "").strip()
        price = request.form.get("price") or "0"
        qty = request.form.get("qty") or "0"
        unit = request.form.get("unit") or "ชิ้น"
        record = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": session.get("username", "ผู้ใช้งาน"),
            "recorder": recorder,
            "code": code,
            "name": name,
            "price": price,
            "qty": qty,
            "unit": unit
        }
        STOCK_LOGS.append(record)
        status_msg = f"บันทึกการนับสต็อก {name} จำนวน {qty} {unit} โดย {recorder} เรียบร้อยแล้ว ใช้สำหรับบันทึกการนับเท่านั้น ไม่ปรับข้อมูลสต็อกหลัก"

    current_recorder = session.get("recorder", "")
    options_html = "".join(
        [f'<option value="{c}">{c} - {p["name"]}</option>' for c, p in PRODUCTS.items()]
    )
    logs_html = "".join(
        [f'<li>{r["time"]} | ผู้ใช้ {r["user"]} | ผู้บันทึกหรือผู้นับสต็อก {r["recorder"]} | รหัส {r["code"]} | {r["name"]} | ราคา {r["price"]} | จำนวน {r["qty"]} {r["unit"]}</li>' for r in reversed(STOCK_LOGS)]
    )

    html = f"""
    <section class="card">
      <div style="display:flex; justify-content:space-between; align-items:center; gap:6px; flex-wrap:wrap;">
        <h2 style="margin:0;">นับสต็อก</h2>
        <span style="font-size:12px; color:#475569;">ผู้ใช้: <strong>{session.get("username", "-")}</strong> | ผู้นับ: <strong>{current_recorder or "-"}</strong></span>
      </div>
      <p class="hint-mobile-hide">ใช้สำหรับกรอกข้อมูลเพื่อบันทึกการนับสต็อกเท่านั้น ไม่สามารถใช้ปรับข้อมูลสต็อกหลักได้</p>
      {SCANNER_BLOCK}
      <form method="post" id="stockForm" autocomplete="off">
        <div class="form-grid-2">
          <div>
            <label>ชื่อผู้นับสต็อก</label>
            <input id="recorderInput" name="recorder" type="text" value="{current_recorder}" autocomplete="off" required />
          </div>
          <div>
            <label>เลือกรหัสสินค้า</label>
            <select id="barcodePicker" onchange="lookupBarcode(this.value)">
              <option value="">เลือกรหัส</option>
              {options_html}
            </select>
          </div>
        </div>
        <div class="form-grid-2">
          <div>
            <label>รหัสสินค้า บาร์โค้ด</label>
            <input id="codeInput" name="code" type="text" required onchange="lookupBarcode(this.value)" />
          </div>
          <div>
            <label>ชื่อสินค้า</label>
            <input id="nameInput" name="name" type="text" required />
          </div>
        </div>
        <div class="form-grid-3">
          <div>
            <label>ราคา</label>
            <input id="priceInput" name="price" type="number" step="any" required />
          </div>
          <div>
            <label>จำนวน</label>
            <input id="qtyInput" name="qty" type="number" step="any" required />
          </div>
          <div>
            <label>หน่วย</label>
            <select id="unitInput" name="unit">
              <option value="ชิ้น">ชิ้น</option>
              <option value="แพ็ค">แพ็ค</option>
              <option value="กล่อง">กล่อง</option>
              <option value="ขวด">ขวด</option>
              <option value="ลัง">ลัง</option>
            </select>
          </div>
        </div>
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
        <div class="form-grid-2">
          <div>
            <label>รหัสสินค้า</label>
            <input id="pricingCodeInput" name="code" type="text" required />
          </div>
          <div>
            <label>ชื่อสินค้า</label>
            <input id="pricingNameInput" name="name" type="text" required />
          </div>
        </div>
        <div class="form-grid-3">
          <div>
            <label>ราคา</label>
            <input id="pricingPriceInput" name="price" type="number" step="any" required />
          </div>
          <div>
            <label>จำนวน</label>
            <input id="pricingQtyInput" name="qty" type="number" step="any" required />
          </div>
          <div>
            <label>หน่วย</label>
            <select id="pricingUnitInput" name="unit">
              <option value="ชิ้น">ชิ้น</option>
              <option value="แพ็ค">แพ็ค</option>
              <option value="กล่อง">กล่อง</option>
              <option value="ขวด">ขวด</option>
              <option value="ลัง">ลัง</option>
            </select>
          </div>
        </div>
        <label>รายละเอียดสินค้า</label>
        <textarea name="detail" rows="1"></textarea>
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

    if request.method == "POST":
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file, full_path, mimetype, pdf_bytes = generate_export_file(current_user, ts)
        EXPORT_AUDITS.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": current_user,
            "type": "PDF",
            "backup": export_file
        })
        return send_file(io.BytesIO(pdf_bytes), mimetype=mimetype, as_attachment=True, download_name=export_file)

    visible_audits = [a for a in EXPORT_AUDITS if can_access_audit(a, current_user)]
    audit_html = "".join(
        [f'<li>{a["time"]} | ผู้ใช้ {a["user"]} | ประเภท {a["type"]} | ไฟล์ส่งออก <a href="/backups/{a["backup"]}">{a["backup"]}</a></li>' for a in reversed(visible_audits)]
    )
    scope_text = "ผู้ดูแลระบบ: เข้าถึงไฟล์สำรองของทุกคนได้" if is_admin_user(current_user) else f"ผู้ใช้ {current_user}: เข้าถึงได้เฉพาะไฟล์สำรองของตัวเอง"

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
        <div class="watermark-text">ระบบนับสต็อก Developed by MJ</div>
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


@app.route("/backups/<filename>")
def download_backup(filename):
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    current_user = session.get("username", "ผู้ดูแลระบบ")
    matched = next((a for a in EXPORT_AUDITS if a.get("backup") == filename), None)
    if matched and not can_access_audit(matched, current_user):
        return "ไม่มีสิทธิ์เข้าถึงไฟล์สำรองของผู้ใช้อื่น", 403
    if not is_admin_user(current_user) and f"_{current_user}_" not in filename:
        return "ไม่มีสิทธิ์เข้าถึงไฟล์สำรองของผู้ใช้อื่น", 403
    return send_from_directory(BACKUP_DIR, filename, as_attachment=True)


@app.route("/review", methods=["GET", "POST"])
def review_page():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    share_msg = ""
    if request.method == "POST":
        action = request.form.get("action", "submit")
        stars = int(request.form.get("stars") or 5)
        comment = (request.form.get("comment") or "").strip()
        if action == "share":
            preview_text = comment if comment else f"ให้คะแนน {stars} ดาว"
            share_msg = f"เตรียมข้อความสำหรับแชร์เรียบร้อยแล้ว: ระบบนับสต็อก ซอฟต์แวร์ โดย เอ็มเจ ({preview_text})"
        else:
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
      <form method="post" id="reviewForm">
        <label>ให้คะแนน 1 ถึง 5 ดาว</label>
        <select id="reviewStars" name="stars">
          <option value="5">5 ดาว</option>
          <option value="4">4 ดาว</option>
          <option value="3">3 ดาว</option>
          <option value="2">2 ดาว</option>
          <option value="1">1 ดาว</option>
        </select>
        <label>ข้อความรีวิว</label>
        <textarea id="reviewComment" name="comment" rows="3" placeholder="เขียนรีวิวการใช้งานระบบ"></textarea>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
          <button type="submit" name="action" value="submit">ส่งรีวิว</button>
          <button type="button" id="shareBtn" class="secondary" onclick="handleShareAction()">แชร์ไปยังช่องทางอื่น</button>
        </div>
      </form>
      <div id="shareBox" style="margin-top:12px;">
        <p id="shareStatus" class="msg-ok">{share_msg}</p>
        <textarea id="shareTextArea" rows="2" readonly style="display:none; background:#f8fafc;"></textarea>
        <div id="shareLinks" style="display:none; gap:8px; flex-wrap:wrap; margin-top:6px;">
          <a id="lineShareLink" class="nav-btn secondary" target="_blank" rel="noopener">แชร์ไปที่ LINE</a>
          <a id="fbShareLink" class="nav-btn secondary" target="_blank" rel="noopener">แชร์ไปที่ Facebook</a>
        </div>
      </div>
      <ul style="margin-top:14px;">{reviews_html}</ul>
    </section>
    <script>
      async function handleShareAction() {{
        const stars = document.getElementById('reviewStars').value;
        const comment = document.getElementById('reviewComment').value.trim();
        const appUrl = window.location.origin + '/';
        const shareMsg = 'ชวนมาใช้งานระบบนับสต็อก ซอฟต์แวร์ โดย เอ็มเจ เข้าใช้งานได้ที่ลิงก์นี้เลยครับ ' + appUrl + ' (รีวิว ' + stars + ' ดาว' + (comment ? ': ' + comment : '') + ')';

        const statusEl = document.getElementById('shareStatus');
        const areaEl = document.getElementById('shareTextArea');
        const linksEl = document.getElementById('shareLinks');
        const lineEl = document.getElementById('lineShareLink');
        const fbEl = document.getElementById('fbShareLink');

        areaEl.style.display = 'block';
        areaEl.value = shareMsg;
        linksEl.style.display = 'flex';
        lineEl.href = 'https://social-plugins.line.me/lineit/share?url=' + encodeURIComponent(appUrl) + '&text=' + encodeURIComponent(shareMsg);
        fbEl.href = 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(appUrl);

        let copied = false;
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          try {{
            await navigator.clipboard.writeText(shareMsg);
            copied = true;
          }} catch (e) {{}}
        }}
        if (!copied) {{
          areaEl.select();
          try {{
            copied = document.execCommand('copy');
          }} catch (e) {{}}
        }}

        if (navigator.share) {{
          try {{
            await navigator.share({{
              title: 'ระบบนับสต็อก ซอฟต์แวร์ โดย เอ็มเจ',
              text: shareMsg,
              url: appUrl
            }});
            statusEl.textContent = 'เปิดหน้าต่างแชร์เรียบร้อยแล้ว และคัดลอกข้อความลงคลิปบอร์ดแล้ว';
            return;
          }} catch (e) {{}}
        }}

        statusEl.textContent = copied
          ? 'คัดลอกข้อความสำหรับแชร์ลงคลิปบอร์ดแล้ว สามารถวางหรือกดปุ่มแชร์ไปยังช่องทางอื่นได้ทันที'
          : 'สร้างข้อความสำหรับแชร์เรียบร้อยแล้ว สามารถคัดลอกจากกล่องด้านล่างหรือกดปุ่มแชร์ได้เลย';
      }}
    </script>
    """
    return render_page(html)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
