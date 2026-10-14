اimport os
import io
import glob
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from weasyprint import HTML

app = FastAPI()

# بيانات بوت تيليجرام
BOT_TOKEN = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
def get_letterhead_path():
    """البحث عن صورة الورقة المروّسة داخل مجلد التطبيق"""
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        files = glob.glob(ext)
        if files:
            return os.path.abspath(files[0])
    return None

def generate_pdf(content_text: str, title: str = "مستند رسمي") -> io.BytesIO:
    """توليد ملف PDF احترافي يدعم اللغة العربية مع الورقة المروّسة"""
    bg_path = get_letterhead_path()
    bg_style = f"background-image: url('file://{bg_path}'); background-size: cover; background-repeat: no-repeat;" if bg_path else ""

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 0;
            }}
            body {{
                font-family: 'Noto Sans Arabic', 'DejaVu Sans', sans-serif;
                margin: 0;
                padding: 130px 50px 100px 50px;
                box-sizing: border-box;
                direction: rtl;
                color: #222;
                font-size: 14px;
                line-height: 1.8;
                {bg_style}
            }}
            .title {{
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                color: #0b3954;
                margin-bottom: 25px;
                border-bottom: 2px solid #0b3954;
                padding-bottom: 8px;
            }}
            .content {{
                white-space: pre-wrap;
                text-align: justify;
            }}
        </style>
    </head>
    <body>
        <div class="title">{title}</div>
        <div class="content">{content_text}</div>
    </body>
    </html>
    """
    pdf_io = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_io)
    pdf_io.seek(0)
    return pdf_io

def send_telegram_document(chat_id: int, file_bytes: io.BytesIO, filename: str, caption: str):
    """إرسال مستند PDF إلى مستخدم تيليجرام"""
    url = f"{TELEGRAM_API}/sendDocument"
    files = {"document": (filename, file_bytes.getvalue(), "application/pdf")}
    data = {"chat_id": chat_id, "caption": caption}
    requests.post(url, data=data, files=files)

def send_telegram_message(chat_id: int, text: str):
    """إرسال رسالة نصية"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

@app.get("/", response_class=HTMLResponse)
async def home():
    bg_status = "✅ عُثر على الورقة المروّسة" if get_letterhead_path() else "⚠️ لم يتم العثور على صورة مروّسة"
    return f"""
    <div style="font-family: sans-serif; text-align: center; padding: 40px; direction: rtl;">
        <h2>🚀 سيرفر شركة وييفقايد وبوت تيليجرام يعمل بنجاح 24/7</h2>
        <p>الهوية البصرية: <b>{bg_status}</b></p>
    </div>
    """

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """استقبال الرسائل من تيليجرام ومعالجتها"""
    update = await request.json()
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"].strip()

        if text.startswith("/start"):
            msg = (
                "مرحباً بك في نظام وييفقايد للأعمال الهندسية 📄\n\n"
                "أرسل لي أي نص أو تفاصيل فاتورة/خطاب، وسأقوم بتحويلها فوراً إلى مستند PDF معتمد بالهوية الرسمية."
            )
            send_telegram_message(chat_id, msg)
        else:
            send_telegram_message(chat_id, "⏳ جاري إعداد المستند وطباعة الهوية البصرية...")
            try:
                pdf_file = generate_pdf(content_text=text, title="مستند رسمي - شركة وييفقايد")
                send_telegram_document(
                    chat_id=chat_id,
                    file_bytes=pdf_file,
                    filename="Waveguide_Document.pdf",
                    caption="✅ تم توليد المستند بنجاح بالهوية الرسمية."
                )
            except Exception as e:
                send_telegram_message(chat_id, f"حدث خطأ أثناء إنشاء الملف: {str(e)}")

    return JSONResponse(content={"status": "ok"})
