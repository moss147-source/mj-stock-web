with open("app-v10.py", "r", encoding="utf-8") as f:
    src = f.read()

# Replace build_word_docx_bytes and build_excel_csv_bytes so ALL exported contents (including Word/Excel helpers if called anywhere)
# use 100% Thai labels, Thai text, and "Developed by MJ".
old_docx = '''def build_word_docx_bytes(lines):'''
old_csv = '''def build_excel_csv_bytes():'''

s_idx = src.find(old_docx)
e_idx = src.find("def generate_export_file(")

new_helpers = '''def build_word_docx_bytes(lines):
    def xml_esc(s):
        return (
            str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    paragraphs = "".join(
        [f"<w:p><w:r><w:t xml:space=\\"preserve\\">{xml_esc(line)}</w:t></w:r></w:p>" for line in lines]
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraphs}</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)
    buf.seek(0)
    return buf.read()


def build_excel_csv_bytes():
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ลายน้ำ", "ระบบนับสต็อก Developed by MJ"])
    writer.writerow(["รหัสสินค้า", "ชื่อสินค้า", "ราคา", "จำนวน", "หน่วย", "รายละเอียด"])
    for p in PRODUCTS.values():
        writer.writerow([p["code"], p["name"], p["price"], p["qty"], p["unit"], p["detail"]])
    writer.writerow([])
    writer.writerow(["เวลา", "ผู้ใช้", "ผู้นับสต็อก", "รหัสสินค้า", "ชื่อสินค้า", "ราคา", "จำนวน", "หน่วย"])
    for r in STOCK_LOGS:
        writer.writerow([r["time"], r["user"], r["recorder"], r["code"], r["name"], r["price"], r["qty"], r["unit"]])
    return ("\\ufeff" + buf.getvalue()).encode("utf-8")


'''

assert s_idx != -1 and e_idx != -1
updated = src[:s_idx] + new_helpers + src[e_idx:]

with open("app-v10.py", "w", encoding="utf-8") as f:
    f.write(updated)

print("Updated export helpers to pure Thai + Developed by MJ")
