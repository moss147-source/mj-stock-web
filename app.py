with open("app-v10.py", "r", encoding="utf-8") as f:
    src = f.read()

old_header = """  <header>
    <div>ระบบนับสต็อก</div>
    <div>ซอฟต์แวร์ โดย เอ็มเจ</div>
  </header>"""

new_header = """  <header>
    <div>ระบบนับสต็อก</div>
    <div>{{ session.get("username") if session.get("logged_in") else "ซอฟต์แวร์ โดย เอ็มเจ" }}</div>
  </header>"""

assert old_header in src, "old_header not found"
updated = src.replace(old_header, new_header, 1)

with open("app-v10.py", "w", encoding="utf-8") as f:
    f.write(updated)

with open("app-v10-v7.py", "w", encoding="utf-8") as f:
    f.write(updated)

print("Updated top-right header to show username when logged in")
