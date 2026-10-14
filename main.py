import os
import io
import glob
import base64
from datetime import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from weasyprint import HTML

app = FastAPI()

TOKEN = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
K1 = "AQ.Ab8RN6Kpct7KHJYWnDMp"
K2 = "QO9EWqEsN1886rewawWKYqMG-wS7Pg"
GEMINI_KEY = K1 + K2

TG_API = f"https://api.telegram.org/bot{TOKEN}"
TG_FILE = f"https://api.telegram.org/file/bot{TOKEN}"

PROMPT = (
    "أنت النظام الهندسي والإداري لشركة وييفقايد للأعمال الهندسية. "
    "حول طلب المستخدم إلى مستند رسمي متكامل بصيغة HTML داخلية فقط بدون markdown. "
    "1. إذا كان الطلب فاتورة أو عرض سعر أو مستخلص: "
    "ضع العنوان في المنتصف داخل <div class='subj'>، ثم جدول <table> بأعمدة: "
    "(م، البيان / الوصف، الكمية، سعر الوحدة، الإجمالي) مع صف إجمالي أخير مميز. "
    "2. إذا كان الطلب خطاباً رسمياً: "
    "اكتب الجهة الموجه إليها، ثم تحية طيبة، ثم الموضوع، ثم فقرات الخطاب الرصينة."
)

def get_img_b64(is_stamp=False):
    files = glob.glob("*.png") + glob.glob("*.jpg") + glob.glob("*.jpeg")
    for f in files:
        low = f.lower()
        if is_stamp and ("stamp" in low or "sign" in low):
            with open(f, "rb") as fp:
                return base64.b64encode(fp.read()).decode()
        if not is_stamp and "stamp" not in low and "sign" not in low:
            with open(f, "rb") as fp:
                return base64.b64encode(fp.read()).decode()
    return None

def ask_gemini(text="", audio_b64=None):
    parts = [{"text": PROMPT}]
    if audio_b64:
        parts.append({
            "inline_data": {
                "mime_type": "audio/ogg",
                "data": audio_b64
            }
        })
    if text:
        parts.append({"text": f"تفاصيل الطلب: {text}"})

    for model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model}:generateContent?key={GEMINI_KEY}"
        )
        try:
            r = requests.post(
                url,
                json={"contents": [{"parts": parts}]},
                timeout=30
            )
            if r.ok:
                res = r.json()
                out = res["candidates"][0]["content"]["parts"][0]["text"]
                out = out.replace("```html", "").replace("```", "")
                return out.strip(), None
            err = r.text
        except Exception as e:
            err = str(e)
    return None, err

def make_pdf(body_html: str):
    bg_b64 = get_img_b64(is_stamp=False)
    st_b64 = get_img_b64(is_stamp=True)
    date_s = datetime.now().strftime("%Y/%m/%dم")

    bg_css = ""
    if bg_b64:
        bg_css = (
            f"background: url('data:image/png;base64,{bg_b64}') "
            "no-repeat center; background-size: 210mm 297mm;"
        )

    stamp_html = ""
    if st_b64:
        stamp_html = (
            f"<img src='data:image/png;base64,{st_b64}' "
            "style='width:135px;margin-top:4px;'/>"
        )

    html = (
        "<!DOCTYPE html><html dir='rtl' lang='ar'><head><meta charset='utf-8'>"
        "<style>"
        f"@page {{ size: A4; margin: 0; {bg_css} }}"
        "body { font-family: 'Noto Sans Arabic', sans-serif; margin: 0;"
        " padding: 145px 45px 115px 45px; direction: rtl; color: #111;"
        " font-size: 14px; line-height: 1.8; }"
        ".basmala { text-align: center; font-weight: bold;"
        " font-size: 15px; margin-bottom: 10px; }"
        ".date-row { text-align: right; font-weight: bold;"
        " font-size: 13.5px; margin-bottom: 15px; }"
        ".subj { text-align: center; font-size: 17px; font-weight: bold;"
        " color: #0C564C; text-decoration: underline; margin: 15px 0; }"
        "p { text-align: justify; margin: 8px 0; }"
        "table { width: 100%; border-collapse: collapse; margin: 15px 0; }"
        "th { background: #0C564C; color: #fff; padding: 9px;"
        " border: 1px solid #0C564C; border-bottom: 3px solid #F5B800;"
        " font-size: 13.5px; }"
        "td { padding: 8px; border: 1px solid #cbd5e1; text-align: center; }"
        "tr:nth-child(even) { background: #f8fafc; }"
        "tr:last-child { font-weight: bold; background: #f1f5f9;"
        " border-bottom: 3px double #0C564C; }"
        ".sig { margin-top: 40px; text-align: left; padding-left: 20px; }"
        ".sig-box { display: inline-block; text-align: center;"
        " font-weight: bold; line-height: 1.6; }"
        "</style></head><body>"
        "<div class='basmala'>بسم الله الرحمن الرحيم</div>"
        f"<div class='date-row'>التاريخ: {date_s}</div>"
        f"<div class='content'>{body_html}</div>"
        "<div class='sig'><div class='sig-box'>"
        "المدير العام<br>مهندس حسن طارق عامر بابكر<br>"
        f"{stamp_html}</div></div></body></html>"
    )

    buf = io.BytesIO()
    HTML(string=html).write_pdf(buf)
    buf.seek(0)
    return buf, (bg_b64 is not None)

def send_msg(cid, txt):
    requests.post(
        f"{TG_API}/sendMessage",
        json={"chat_id": cid, "text": txt},
        timeout=10
    )

def send_doc(cid, buf, cap):
    files = {"document": ("Waveguide_Official.pdf", buf.getvalue(), "application/pdf")}
    requests.post(
        f"{TG_API}/sendDocument",
        data={"chat_id": cid, "caption": cap},
        files=files,
        timeout=40
    )

@app.get("/")
def home():
    has_bg = get_img_b64(False) is not None
    st = "✅ مرفوعة وجاهزة" if has_bg else "⚠️ لم يتم رفع صورة الترويسة في GitHub"
    return HTMLResponse(
        "<div style='text-align:center;direction:rtl;padding:30px;'>"
        "<h2>سيرفر وييفقايد يعمل 24/7</h2>"
        f"<p>حالة الورقة المروّسة: <b>{st}</b></p></div>"
    )

@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        msg = data.get("message", {})
        cid = msg.get("chat", {}).get("id")
        if not cid:
            return JSONResponse({"ok": True})

        text = msg.get("text", "").strip()
        if text.startswith("/start"):
            send_msg(
                cid,
                "مرحباً بك في نظام وييفقايد للأعمال الهندسية 📄✨\n"
                "أرسل تفاصيل الفاتورة أو الخطاب نصياً أو صوتياً."
            )
            return JSONResponse({"ok": True})

        audio_b64 = None
        if "voice" in msg:
            send_msg(cid, "🎙️ جاري الاستماع للتسجيل وتجهيز المستند...")
            fid = msg["voice"]["file_id"]
            r1 = requests.get(f"{TG_API}/getFile?file_id={fid}").json()
            fpath = r1["result"]["file_path"]
            raw = requests.get(f"{TG_FILE}/{fpath}").content
            audio_b64 = base64.b64encode(raw).decode()
        elif text:
            send_msg(cid, "⏳ جاري صياغة وتوليد المستند بالهوية الرسمية...")
        else:
            return JSONResponse({"ok": True})

        ai_html, err = ask_gemini(text=text, audio_b64=audio_b64)
        if not ai_html:
            if audio_b64:
                send_msg(cid, f"⚠️ تعذر تحليل الصوت:\n{err}")
                return JSONResponse({"ok": True})
            paras = [f"<p>{p}</p>" for p in text.split("\n") if p.strip()]
            ai_html = "".join(paras)

        pdf, has_bg = make_pdf(ai_html)
        note = "" if has_bg else "\n⚠️ ملاحظة: ارفع صورة الترويسة في GitHub لتظهر الخلفية."
        send_doc(cid, pdf, f"✅ تم إصدار المستند بنجاح.{note}")

    except Exception as e:
        if "cid" in locals() and cid:
            send_msg(cid, f"⚠️ خطأ: {e}")
    return JSONResponse({"ok": True})
