import os
import io
import glob
import logging
from datetime import datetime
import requests

# معالجة تعارض مكتبة pydyf مع WeasyPrint تلقائياً
try:
    import pydyf
    _orig_pydyf_init = pydyf.PDF.__init__
    def _patched_pydyf_init(self, *args, **kwargs):
        try:
            _orig_pydyf_init(self, *args, **kwargs)
        except TypeError:
            _orig_pydyf_init(self)
            if args:
                if len(args) >= 1:
                    self.version = args[0]
                if len(args) >= 2:
                    self.identifier = args[1]
    pydyf.PDF.__init__ = _patched_pydyf_init
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from weasyprint import HTML

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waveguide-bot")

app = FastAPI(title="Waveguide Bot Service")

BOT_TOKEN = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_letterhead_path():
    """البحث عن صورة الورقة المروّسة الرسمية داخل مجلد المشروع"""
    candidates = [
        "waveguide-letterhead.png",
        "waveguide-letterhead.jpg",
        "letterhead.png",
        "letterhead.jpg"
    ]
    for filename in candidates:
        if os.path.exists(filename):
            return os.path.abspath(filename)
    
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        found = glob.glob(ext)
        if found:
            return os.path.abspath(found[0])
    return None

def generate_pdf(content_text: str, title: str = "مستند رسمي") -> io.BytesIO:
    """توليد ملف PDF احترافي يدعم اللغة العربية مع الورقة المروّسة بدقة A4"""
    bg_path = get_letterhead_path()
    bg_css = f"background-image: url('file://{bg_path}'); background-size: 210mm 297mm; background-repeat: no-repeat;" if bg_path else ""
    current_date = datetime.now().strftime("%Y/%m/%dم")

    paragraphs = content_text.strip().split("\n")
    body_paragraphs = "".join([f"<p>{p}</p>" if p.strip() else "<br/>" for p in paragraphs])

    html_code = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{
    font-family: 'Noto Sans Arabic', 'DejaVu Sans', sans-serif;
    margin: 0;
    padding: 135px 50px 115px 50px;
    direction: rtl;
    color: #222222;
    font-size: 14px;
    line-height: 1.9;
    {bg_css}
}}
.meta-bar {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
    font-size: 13px;
    color: #444444;
    border-bottom: 1px dashed #0C564C;
    padding-bottom: 8px;
}}
.doc-title {{
    text-align: center;
    font-size: 20px;
    font-weight: bold;
    color: #0C564C;
    margin: 15px 0 25px 0;
    padding-bottom: 6px;
    border-bottom: 2px solid #F5B800;
}}
.content {{
    text-align: justify;
    word-wrap: break-word;
}}
.content p {{ margin: 8px 0; }}
.signature-box {{
    margin-top: 45px;
    text-align: left;
    direction: ltr;
    padding-left: 20px;
}}
.signature-inner {{
    display: inline-block;
    text-align: center;
    direction: rtl;
}}
.signature-role {{ font-weight: bold; color: #0C564C; margin-bottom: 5px; }}
.signature-name {{ font-size: 13px; color: #333333; }}
</style>
</head>
<body>
<div class="meta-bar">
    <span>التاريخ: {current_date}</span>
    <span>شركة وييفقايد للأعمال الهندسية</span>
</div>
<div class="doc-title">{title}</div>
<div class="content">
    {body_paragraphs}
</div>
<div class="signature-box">
    <div class="signature-inner">
        <div class="signature-role">الإدارة العامة</div>
        <div class="signature-name">وييفقايد للأعمال الهندسية</div>
    </div>
</div>
</body>
</html>"""

    pdf_io = io.BytesIO()
    HTML(string=html_code).write_pdf(pdf_io)
    pdf_io.seek(0)
    return pdf_io

def send_telegram_message(chat_id: int, text: str):
    """إرسال رسالة نصية إلى المستخدم"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Error in send_telegram_message: {e}")

def send_telegram_document(chat_id: int, file_bytes: io.BytesIO, filename: str, caption: str):
    """إرسال ملف PDF للمستخدم عبر تيليجرام"""
    url = f"{TELEGRAM_API}/
