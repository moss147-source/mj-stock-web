# ระบบนับสต็อก ซอฟต์แวร์ โดย เอ็มเจ

## วิธีนำไปรันบน Render
1. สร้าง Repository ใหม่บน GitHub แล้วอัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้ (`app.py`, `requirements.txt`, `Procfile`, `README.md`)
2. เข้าสู่ระบบ Render แล้วเลือก New -> Web Service และเชื่อมต่อ Repository ที่สร้างไว้
3. ตั้งค่า Build Command เป็น `pip install -r requirements.txt`
4. ตั้งค่า Start Command เป็น `gunicorn app:app`
5. กด Create Web Service แล้วรอจนสถานะเป็น Live เพื่อเปิดใช้งานหน้าเว็บ
