import os
import io
import glob
from datetime import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from weasyprint import HTML

# حل تعارض مكتبة pydyf
try:
    import pydyf
    _orig_init = pydyf.PDF.__init__
    def _safe_init(self, *a, **kw):
        try:
            _orig_init(self, *a, **kw)
        except TypeError:
            _orig_init(self)
            if a:
                self.version = a[0]
            if len(a) > 1:
                self.identifier = a[1]
    pydyf.PDF.__init__ = _safe_init
except Exception:
    pass

app = FastAPI()
TOKEN = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

def get_bg():
    for f in ["waveguide-letterhead.png", "letterhead.png"] + glob.glob("*.png"):
        if os.path.exists(f):
            return os.path.abspath(f)
    return None

def make_pdf(text: str, title: str):
    bg = get_bg()
    bg_style = f"background: url('file://{bg}') no-repeat; background-size: 210mm 297mm;" if bg else ""
    date_str = datetime.now().strftime("%Y/%m/%dم")
    paras = "".join([f"<p>{p}</p>" if p.strip() else "<br/>" for p in text.strip().split("\n")])

    html = f"""<!DOCTYPE html><html dir="rtl"><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 0; }}
body {{ font-family: 'Noto Sans Arabic', sans-serif; margin: 0; padding: 135px 50px 100px 50px; direction: rtl; {bg_style} font-size: 14px; line-height: 1.8; color: #222; }}
.bar {{ display: flex; justify-content: space-between; font-size: 13px; border-bottom: 1px dashed #0C564C; padding-bottom: 6px; margin-bottom: 20px; }}
.title {{ text-align: center; font-size: 19px; font-weight: bold; color: #0C564C; border-bottom: 2px solid #F5B800; padding-bottom: 5px; margin-bottom: 20px; }}
.content {{ text-align: justify; word-wrap: break-word; }}
.sig {{ margin-top: 40px; text-align: left; padding-left: 30px; }}
.sig-in {{ display: inline-block; text-align: center; font-weight: bold; color: #0C564C; }}
</style></head><body>
<div class="bar"><span>التاريخ: {date_str}</span><span>شركة وييفقايد للأعمال الهندسية</span></div>
<div class="title">{title}</div>
<div class="content">{paras}</div>
<div class="sig"><div class="sig-in">الإدارة العامة<br><span style="font-size:12px;color:#444;">وييفقايد للأعمال الهندسية</span></div></div>
</body></html>"""

    buf = io.BytesIO()
    HTML(string=html).write_pdf(buf)
    buf.seek(0)
    return buf

def send_msg(chat_id, text):
    requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)

def send_doc(chat_id, buf, fname, cap):
    files = {"document": (fname, buf.getvalue(), "application/pdf")}
    requests.post(f"{API_URL}/sendDocument", data={"chat_id": chat_id, "caption": cap}, files=files, timeout=40)

@app.get("/")
def home():
    return HTMLResponse("<h2 style='text-align:center;direction:rtl;'>سيرفر وييفقايد يعمل بنجاح 24/7 ✅</h2>")

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        msg = data.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        if not chat_id:
            return JSONResponse({"ok": True})

        if "voice" in msg or "audio" in msg:
            send_msg(chat_id, "🎙️ يرجى إرسال تفاصيل المستند كنص مكتوب لطباعته فوراً.")
            return JSONResponse({"ok": True})

        text = msg.get("text", "")
        if not text:
            return JSONResponse({"ok": True})

        if text.startswith("/start"):
            send_msg(chat_id, "مرحباً بك في نظام وييفقايد 📄✨\nأرسل نص الخطاب أو الفاتورة لتوليد مستند PDF فوري.")
            return JSONResponse({"ok": True})

        send_msg(chat_id, "⏳ جاري توليد المستند بالهوية الرسمية...")
        title = "فاتورة أعمال هندسية" if "فاتورة" in text else "مستند رسمي - وييفقايد"
        pdf = make_pdf(text, title)
        send_doc(chat_id, pdf, "Waveguide_Document.pdf", "✅ تم إصدار المستند بنجاح بالهوية الرسمية.")
    except Exception as e:
        if "chat_id" in locals() and chat_id:
            send_msg(chat_id, f"⚠️ خطأ أثناء المعالجة: {e}")
    return JSONResponse({"ok": True})
