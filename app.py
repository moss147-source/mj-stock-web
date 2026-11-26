with open("app-v10.py", "r", encoding="utf-8") as f:
    src = f.read()

# Replace "พัฒนาโดย เอ็มเจ" with "Developed by MJ" across the app, PDF watermark, and export lines
updated = src.replace("พัฒนาโดย เอ็มเจ", "Developed by MJ")

# Also check if there are any other occurrences of เอ็มเจ or พัฒนาโดย
for kw in ["เอ็มเจ", "พัฒนาโดย"]:
    print(kw, "in updated ->", kw in updated)

with open("app-v10.py", "w", encoding="utf-8") as f:
    f.write(updated)

print("Updated watermark to Developed by MJ in app-v10.py")
