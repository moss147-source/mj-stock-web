import os
import io
import csv
import json
import datetime
import zipfile
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
    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    th, td { border: 1px solid #d9e0e8; padding: 8px 10px; text-align: left; font-size: 14px; }
    th { background: #f8fafc; }
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
