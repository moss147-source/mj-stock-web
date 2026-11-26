import os

print("Files in cwd:", os.listdir("."))

with open("app-v10.py", "r", encoding="utf-8") as f:
    src = f.read()

idx = src.find("export")
while idx != -1:
    start = max(0, idx - 120)
    end = min(len(src), idx + 220)
    print("--- MATCH ---")
    print(src[start:end])
    idx = src.find("export", idx + 1)
