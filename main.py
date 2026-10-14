import os
import io
import glob
import logging
from datetime import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from weasyprint import HTML

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waveguide-bot")

app = FastAPI(title="Waveguide Bot Service")

BOT_TOKEN = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_letterhead_path():
    """البحث عن صورة الورقة المروّسة الرسمية داخل المجلد"""
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
    """توليد ملف PDF احترافي يدعم اللغة العربية مع الورقة المروّسة"""
    bg_path = get_letterhead_path()
    bg_style = f"background-image: url('file://{bg_path}'); background-size: 210mm 297mm; background-repeat: no-repeat;" if bg_path else ""
    current_date = datetime.now().strftime("%Y/%m/%dم")

    paragraphs = content_text.strip().split("\n")
    body_paragraphs = "".join([f"<p>{p}</p>" if p.strip() else "<br/>" for p in paragraphs])

    html_code = (
        '<!DOCTYPE html>'
        '<html lang="ar" dir="rtl">'
        '<head>'
        '<meta charset="UTF-8">'
        '<style>'
        '@page { size: A4; margin: 0; }'
        'body {'
        '  font-family: "Noto Sans Arabic", "DejaVu Sans", sans-serif;'
        '  margin: 0;'
        '  padding: 135px 50px 115px 50px;'
        '  box-sizing: border-box;'
        '  direction: rtl;'
        '  color: #222222;'
        '  font-size: 14px;'
        '  line-height: 1.9;'
        '  ' + bg_style +
        '}'
        '.meta-bar {'
        '  display: flex;'
        '  justify-content: space-between;'
        '  margin-bottom: 20px;'
        '  font-size: 13px;'
        '  color: #444444;'
        '  border-bottom: 1px dashed #0C564C;'
        '  padding-bottom: 8px;'
        '}'
        '.doc-title {'
        '  text-align: center;'
        '  font-size: 20px;'
        '  font-weight: bold;'
        '  color: #0C564C;'
        '  margin: 15px 0 25px 0;'
        '  padding-bottom: 6px;'
        '  border-bottom: 2px solid #F5B800;'
        '}'
        '.content {'
        '  text-align: justify;'
        '  word-wrap: break-word;'
        '}'
        '.content p { margin: 8px 0; }'
        '.signature-box {'
        '  margin-top: 45px;'
        '  text-align: left;'
        '  direction: ltr;'
        '  padding-left: 20px;'
        '}'
        '.signature-inner {'
        '  display: inline-block;'
        '  text-align: center;'
        '  direction: rtl;'
        '}'
        '.signature-role { font-weight: bold; color: #0C564C; margin-bottom: 5px; }'
        '.signature-name { font-size: 13px; color: #333333; }'
        '</style>'
        '</head>'
        '<body>'
        '<div class="meta-bar">'
        f'<span>التاريخ: {current_date}</span>'
        '<span>شركة وييفقايد للأعمال الهندسية</span>'
        '</div>'
        f'<div class="doc-title">{title}</div>'
        f'<div class="content">{body_paragraphs}</div>'
        '<div class="signature-box">'
        '<div class="signature-inner">'
        '<div class="signature-role">الإدارة العامة</div>'
        '<div class="signature-name">وييفقايد للأعمال الهندسية</div>'
        '</div>'
        '</div>'
        '</body>'
        '</html>'
    )

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
    url = f"{TELEGRAM_API}/sendDocument"
    files = {"document": (filename, file_bytes.getvalue(), "application/pdf")}
    data = {"chat_id": chat_id, "caption": caption}
    try:
        resp = requests.post(url, data=data, files=files, timeout=40)
        if not resp.ok:
            logger.error(f"Telegram upload error: {resp.text}")
            send_telegram_message(chat_id, f"⚠️ خطأ تيليجرام أثناء الإرسال: {resp.text}")
    except Exception as e:
        logger.error(f"Error in send_telegram_document: {e}")
        send_telegram_message(chat_id, f"⚠️ تعذر رفع المستند: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def home():
    bg_file = get_letterhead_path()
    bg_name = os.path.basename(bg_file) if bg_file else "لم يتم العثور على صورة مروّسة"
    return (
        '<div style="font-family: sans-serif; text-align: center; padding: 40px; direction: rtl;">'
        '<h2 style="color: #0C564C;">🚀 خادم شركة وييفقايد يعمل بنجاح 24/7</h2>'
        f'<p>حالة الهوية البصرية: <b>{bg_name}</b></p>'
        '</div>'
    )

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """استقبال رسائل تيليجرام ومعالجتها"""
    try:
        update = await request.json()
        if "message" not in update:
            return JSONResponse(content={"status": "no_message"})

        message = update["message"]
        chat_id = message["chat"]["id"]

        if "voice" in message or "audio" in message:
            send_telegram_message(
                chat_id,
                "🎙️ أهلاً بك! يرجى إرسال تفاصيل الفاتورة أو الخطاب كنص مكتوب لطباعته في مستند رسمي فوراً."
            )
            return JSONResponse(content={"status": "ok"})

        if "text" not in message:
            return JSONResponse(content={"status": "unsupported_media"})

        text = message["text"].strip()

        if text.startswith("/start"):
            welcome = (
                "مرحباً بك في نظام شركة وييفقايد للأعمال الهندسية 📄✨\n\n"
                "أرسل لي نص الخطاب أو تفاصيل الفاتورة، وسأقوم بتحويلها فوراً إلى مستند PDF معتمد بالهوية الرسمية."
            )
            send_telegram_message(chat_id, welcome)
            return JSONResponse(content={"status": "ok"})

        send_telegram_message(chat_id, "⏳ جاري إعداد وتوليد المستند بالهوية البصرية المعتمدة...")

        try:
            doc_title = "فاتورة أعمال هندسية" if "فاتورة" in text else "مستند رسمي - وييفقايد"
            pdf_file = generate_pdf(content_text=text, title=doc_title)

            send_telegram_document(
                chat_id=chat_id,
                file_bytes=pdf_file,
                filename="Waveguide_Official_Document.pdf",
                caption="✅ تم إصدار المستند بنجاح بالهوية الرسمية لشركة وييفقايد للأعمال الهندسية."
            )
        except Exception as gen_err:
            logger.error(f"Generation error: {gen_err}", exc_info=True)
            send_telegram_message(chat_id, f"⚠️ حدث خطأ داخلي أثناء إنشاء الملف:\n{str(gen_err)}")

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)

    return JSONResponse(content={"status": "ok"})
