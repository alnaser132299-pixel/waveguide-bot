import os
import io
import glob
import logging
from datetime import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

# إصلاح تلقائي لتعارض مكتبة pydyf مع WeasyPrint
try:
    import pydyf
    _orig_pdf_init = pydyf.PDF.__init__
    def _safe_pdf_init(self, *args, **kwargs):
        try:
            _orig_pdf_init(self, *args, **kwargs)
        except TypeError:
            _orig_pdf_init(self)
    pydyf.PDF.__init__ = _safe_pdf_init
except Exception:
    pass

from weasyprint import HTML

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waveguide")

app = FastAPI()

TOKEN = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
API_URL = "https://api.telegram.org/bot" + TOKEN
URL_MSG = API_URL + "/sendMessage"
URL_DOC = API_URL + "/sendDocument"

def get_bg():
    for name in ["waveguide-letterhead.png", "letterhead.png"]:
        if os.path.exists(name):
            return os.path.abspath(name)
    for ext in ["*.png", "*.jpg"]:
        found = glob.glob(ext)
        if found:
            return os.path.abspath(found[0])
    return None

def generate_pdf(text: str, title: str = "مستند رسمي"):
    bg = get_bg()
    bg_css = ""
    if bg:
        bg_css = "background-image: url('file://" + bg + "'); background-size: 210mm 297mm; background-repeat: no-repeat;"
    
    today = datetime.now().strftime("%Y/%m/%dم")
    lines = text.strip().split("\n")
    paras = "".join(["<p>" + line + "</p>" if line.strip() else "<br/>" for line in lines])

    html = (
        '<!DOCTYPE html>'
        '<html lang="ar" dir="rtl">'
        '<head>'
        '<meta charset="UTF-8">'
        '<style>'
        '@page { size: A4; margin: 0; }'
        'body {'
        ' font-family: "Noto Sans Arabic", "DejaVu Sans", sans-serif;'
        ' margin: 0; padding: 135px 50px 115px 50px;'
        ' box-sizing: border-box; direction: rtl;'
        ' color: #222; font-size: 14px; line-height: 1.9;'
        + bg_css +
        '}'
        '.bar {'
        ' display: flex; justify-content: space-between;'
        ' margin-bottom: 20px; font-size: 13px; color: #444;'
        ' border-bottom: 1px dashed #0C564C; padding-bottom: 8px;'
        '}'
        '.title {'
        ' text-align: center; font-size: 20px; font-weight: bold;'
        ' color: #0C564C; margin: 15px 0 25px 0; padding-bottom: 6px;'
        ' border-bottom: 2px solid #F5B800;'
        '}'
        '.content { text-align: justify; word-wrap: break-word; }'
        '.content p { margin: 8px 0; }'
        '.sig { margin-top: 45px; text-align: left; direction: ltr; padding-left: 20px; }'
        '.sig-in { display: inline-block; text-align: center; direction: rtl; }'
        '.role { font-weight: bold; color: #0C564C; margin-bottom: 5px; }'
        '.name { font-size: 13px; color: #333; }'
        '</style>'
        '</head>'
        '<body>'
        '<div class="bar">'
        '<span>التاريخ: ' + today + '</span>'
        '<span>شركة وييفقايد للأعمال الهندسية</span>'
        '</div>'
        '<div class="title">' + title + '</div>'
        '<div class="content">' + paras + '</div>'
        '<div class="sig">'
        '<div class="sig-in">'
        '<div class="role">الإدارة العامة</div>'
        '<div class="name">وييفقايد للأعمال الهندسية</div>'
        '</div>'
        '</div>'
        '</body>'
        '</html>'
    )

    buf = io.BytesIO()
    HTML(string=html).write_pdf(buf)
    buf.seek(0)
    return buf

def send_msg(chat_id: int, text: str):
    try:
        requests.post(URL_MSG, json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        logger.error(f"msg err: {e}")

def send_doc(chat_id: int, buf: io.BytesIO, fname: str, cap: str):
    try:
        files = {"document": (fname, buf.getvalue(), "application/pdf")}
        data = {"chat_id": chat_id, "caption": cap}
        r = requests.post(URL_DOC, data=data, files=files, timeout=40)
        if not r.ok:
            send_msg(chat_id, "⚠️ تيليجرام رفض الملف: " + r.text)
    except Exception as e:
        send_msg(chat_id, "⚠️ فشل رفع الملف: " + str(e))

@app.get("/", response_class=HTMLResponse)
async def home():
    bg = get_bg()
    st = os.path.basename(bg) if bg else "غير متوفرة"
    return (
        '<div style="text-align:center;padding:40px;font-family:sans-serif;direction:rtl;">'
        '<h2 style="color:#0C564C;">سيرفر وييفقايد يعمل 24/7</h2>'
        f'<p>الهوية البصرية: <b>{st}</b></p>'
        '</div>'
    )

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        if "message" not in data:
            return JSONResponse({"status": "no_msg"})

        msg = data["message"]
        chat_id = msg["chat"]["id"]

        if "voice" in msg or "audio" in msg:
            send_msg(chat_id, "🎙️ أهلاً بك! يرجى إرسال تفاصيل المستند كنص مكتوب.")
            return JSONResponse({"status": "ok"})

        if "text" not in msg:
            return JSONResponse({"status": "skip"})

        text = msg["text"].strip
