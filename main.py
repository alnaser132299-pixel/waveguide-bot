
import os
import glob
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
from PIL import Image, ImageDraw
import weasyprint

app = FastAPI(title="Waveguide Bot Engine")

STORAGE_DIR = "generated_docs"
os.makedirs(STORAGE_DIR, exist_ok=True)

# 1. كاشف ذكي للتعرف على صورة الورقة المروسة أياً كان اسمها
def get_letterhead_path():
    # البحث عن أي صورة مرفوعة غير الختم
    images = glob.glob("*.png") + glob.glob("*.jpg") + glob.glob("*.jpeg")
    for img in images:
        if "clean_stamp" not in img.lower():
            return os.path.abspath(img)
    return None

LETTERHEAD_PATH = get_letterhead_path()
STAMP_PATH = os.path.abspath("clean_stamp.png")

# 2. توليد ذاتي لختم وتوقيع وييفقايد المعتمد بخلفية شفافة
def ensure_stamp():
    if not os.path.exists(STAMP_PATH):
        img = Image.new("RGBA", (504, 179), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        # إطار الختم الأزرق
        draw.rounded_rectangle([(15, 15), (280, 160)], radius=10, outline="#1b3573", width=4)
        draw.text((35, 105), "وييفقايد للأعمال الهندسية", fill="#1b3573")
        draw.text((30, 128), "Waveguide Engineering Works", fill="#1b3573")
        # رمز الشعار الوسطي
        draw.polygon([(140, 35), (180, 75), (140, 105), (100, 75)], fill="#1b3573")
        # التوقيع المعتمد
        sig_points = [(350, 150), (410, 30), (370, 70), (430, 110), (390, 140), (440, 160), (360, 130), (460, 100)]
        draw.line(sig_points, fill="#3b4252", width=3)
        img.save(STAMP_PATH, "PNG")

ensure_stamp()

# 3. روابط فحص السيرفر والتحميل (Keep-Alive)
@app.get("/")
def home():
    bg_status = "✅ عُثر على الورقة المروّسة" if LETTERHEAD_PATH else "⚠️ لم يتم العثور على صورة الخلفية"
    return HTMLResponse(f"""
    <div style='text-align:center;font-family:sans-serif;margin-top:60px;'>
      <h2 style='color:#0c564c;'>🚀 خادم شركة وييفقايد يعمل بنجاح 24/7</h2>
      <p style='font-size:16px;'>حالة الهوية البصرية: <b>{bg_status}</b></p>
    </div>
    """)

@app.get("/files/{file_name}")
def download_file(file_name: str):
    file_path = os.path.join(STORAGE_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "الملف غير موجود"}

# 4. محرك بناء ملفات الـ PDF
def generate_invoice_pdf(items, customer, inv_no, date, sys_title, has_vat, output_path):
    subtotal = sum(int(it['qty']) * int(it['price']) for it in items)
    vat = round(subtotal * 0.17) if has_vat else 0
    total = subtotal + vat if has_vat else subtotal

    bg_css = f"background-image: url('file://{LETTERHEAD_PATH}');" if LETTERHEAD_PATH else ""

    rows_html = "".join([
        f"<tr class='{'even' if i%2 else 'odd'}'>"
        f"<td style='text-align:center;'>{i+1}</td>"
        f"<td style='text-align:left;'>{it['desc']}</td>"
        f"<td style='text-align:center;'>{it['unit']}</td>"
        f"<td style='text-align:center;'>{it['qty']}</td>"
        f"<td style='text-align:right;'>{int(it['price']):,}</td>"
        f"<td style='text-align:right;'>{(int(it['qty']) * int(it['price'])):,}</td>"
        f"</tr>" for i, it in enumerate(items)
    ])

    tot_html = f"""
    <tr style="background:#fff;"><td colspan="5" style="text-align:center;font-weight:bold;">Subtotal</td><td style="text-align:right;font-weight:bold;">{subtotal:,}</td></tr>
    <tr style="background:#fff;"><td colspan="5" style="text-align:center;font-weight:bold;">VAT (17%)</td><td style="text-align:right;font-weight:bold;">{vat:,}</td></tr>
    <tr style="background:#edf4f2;color:#0c564c;border-bottom:3.5px double #0c564c;">
      <td colspan="5" style="text-align:center;font-weight:bold;">TOTAL</td><td style="text-align:right;font-weight:bold;">{total:,}</td>
    </tr>""" if has_vat else f"""
    <tr style="background:#edf4f2;color:#0c564c;border-bottom:3.5px double #0c564c;">
      <td colspan="5" style="text-align:center;font-weight:bold;">TOTAL</td><td style="text-align:right;font-weight:bold;">{total:,}</td>
    </tr>"""

    html = f"""<!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8">
    <style>
      @page {{ size: A4; margin: 0; {bg_css} background-size: 100% 100%; }}
      body {{ margin: 0; padding: 52mm 20mm 35mm 20mm; font-family: 'Arial', sans-serif; }}
      .hdr {{ width:100%; margin-bottom:4mm; }}
      .hdr td {{ border:none; vertical-align:middle; font-weight:bold; font-size:11.5pt; }}
      .title {{ text-align:center; margin:2mm 0 4mm 0; }}
      .title span {{ font-size:12.5pt; font-weight:bold; text-decoration:underline; color:#0c564c; }}
      table.tbl {{ width:100%; border-collapse:collapse; }}
      table.tbl th {{ background:#0c564c; color:#fff; padding:6px; border-bottom:2.5px solid #f5b800; text-align:center; font-size:10pt; }}
      table.tbl td {{ border:1px solid #c8d1cf; padding:6px 8px; font-size:9.5pt; }}
      .even td {{ background:#f7faf9; }}
      .stamp {{ text-align:center; margin-top:8mm; }}
    </style></head>
    <body>
      <table class="hdr"><tr>
        <td style="width:60%;">Customer: {customer}<br>Date: {date}</td>
        <td style="width:40%; text-align:right;">Invoice No.: {inv_no}</td>
      </tr></table>
      <div class="title"><span>{sys_title}</span></div>
      <table class="tbl">
        <thead><tr><th>No</th><th>Description</th><th>Unit</th><th>QTY</th><th>Unit Price SDG</th><th>Total Price SDG</th></tr></thead>
        <tbody>{rows_html}{tot_html}</tbody>
      </table>
      <div class="stamp"><img src="file://{STAMP_PATH}" style="width:175px;"></div>
    </body></html>"""
    weasyprint.HTML(string=html).write_pdf(output_path)

# 5. استقبال رسائل بوابة الواتساب
@app.post("/webhook")
async def receive_whatsapp(request: Request, bg: BackgroundTasks):
    data = await request.json()
    return {"status": "success"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
