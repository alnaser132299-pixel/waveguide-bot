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
BG_NAME = "1000344641-93003ba8ae050194.jpg"

PROMPT = (
    "أنت النظام الإداري لشركة وييفقايد للأعمال الهندسية. "
    "حول طلب المستخدم إلى مستند رسمي بصيغة HTML داخلية فقط بدون markdown. "
    "للفواتير والمستخلصات: ضع العنوان في <div class='subj'>، "
    "ثم جدول <table> بأعمدة (م، البيان، الكمية، سعر الوحدة، الإجمالي) "
    "مع صف إجمالي أخير. وللخطابات: اكتب الجهة، التحية، الموضوع، والفقرات."
)

def get_bg_b64():
    if os.path.exists(BG_NAME):
        with open(BG_NAME, "rb") as fp:
            return base64.b64encode(fp.read()).decode()
    files = glob.glob("*.jpg") + glob.glob("*.jpeg") + glob.glob("*.png")
    for f in files:
        if "stamp" not in f.lower():
            with open(f, "rb") as fp:
                return base64.b64encode(fp.read()).decode()
    return None

def ask_gemini(text="", audio_b64=None):
    parts = [{"text": PROMPT}]
    if audio_b64:
        parts.append({
            "inline_data": {"mime_type": "audio/ogg", "data": audio_b64}
        })
    if text:
        parts.append({"text": f"الطلب: {text}"})

    for m in ["gemini-2.0-flash", "gemini-1.5-flash"]:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{m}:generateContent?key={GEMINI_KEY}"
        )
        try:
            r = requests.post(
                url, json={"contents": [{"parts": parts}]}, timeout=25
            )
            if r.ok:
                res = r.json()
                out = res["candidates"][0]["content"]["parts"][0]["text"]
                return out.replace("```html", "").replace("```", "").strip()
        except Exception:
            pass
    return None

def format_fallback(text: str):
    lines = [ln.strip() for ln in text.strip().split("\n") if ln.strip()]
    if not lines:
        return "<p></p>"
    title = lines[0]
    body = lines[1:] if len(lines) > 1 else lines
    html = f"<div class='subj'>{title}</div>"
    for p in body:
        html += f"<p>{p}</p>"
    return html

def make_pdf(body_html: str):
    bg_b64 = get_bg_b64()
    date_s = datetime.now().strftime("%Y/%m/%dم")

    bg_tag = ""
    if bg_b64:
        bg_tag = (
            f"<img class='bg' src='data:image/jpeg;base64,{bg_b64}'/>"
        )

    svg_stamp = (
        "<svg width='125' height='125' viewBox='0 0 140 140'>"
        "<circle cx='70' cy='70' r='62' fill='none' "
        "stroke='#0C564C' stroke-width='3.5' stroke-dasharray='4,2'/>"
        "<circle cx='70' cy='70' r='55' fill='none' "
        "stroke='#0C564C' stroke-width='1.5'/>"
        "<text x='70' y='48' text-anchor='middle' fill='#0C564C' "
        "font-size='10' font-weight='bold'>شركة وييفقايد</text>"
        "<text x='70' y='64' text-anchor='middle' fill='#0C564C' "
        "font-size='9.5' font-weight='bold'>للأعمال الهندسية</text>"
        "<line x1='28' y1='73' x2='112' y2='73' "
        "stroke='#F5B800' stroke-width='2'/>"
        "<text x='70' y='88' text-anchor='middle' fill='#0C564C' "
        "font-size='9' font-weight='bold'>WAVEGUIDE ENG.</text>"
        "<text x='70' y='104' text-anchor='middle' fill='#0C564C' "
        "font-size='8'>الإدارة العامة - معتمد</text>"
        "</svg>"
    )

    html = (
        "<!DOCTYPE html><html dir='rtl' lang='ar'><head><meta charset='utf-8'>"
        "<style>"
        "@page { size: A4; margin: 0; }"
        "body { font-family: 'Noto Sans Arabic', sans-serif; margin: 0;"
        " padding: 155px 45px 120px 45px; direction: rtl; color: #111;"
        " font-size: 14px; line-height: 1.8; position: relative; }"
        ".bg { position: fixed; top: 0; left: 0; width: 210mm;"
        " height: 297mm; z-index: -10; }"
        ".basmala { text-align: center; font-weight: bold;"
        " font-size: 15px; margin-bottom: 8px; }"
        ".date-row { text-align: right; font-weight: bold;"
        " font-size: 13.5px; margin-bottom: 14px; color: #0C564C; }"
        ".subj { text-align: center; font-size: 17px; font-weight: bold;"
        " color: #0C564C; background: rgba(248,250,252,0.85);"
        " border-right: 4px solid #F5B800; padding: 6px 12px;"
        " margin: 14px 0; }"
        "p { text-align: justify; margin: 8px 0; }"
        "table { width: 100%; border-collapse: collapse; margin: 15px 0;"
        " background: rgba(255,255,255,0.9); }"
        "th { background: #0C564C; color: #fff; padding: 8px;"
        " border:
