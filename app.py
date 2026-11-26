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
    a.nav-btn, button { padding: 9px
