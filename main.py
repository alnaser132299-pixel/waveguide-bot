import base64, glob, io, os, requests
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from weasyprint import HTML

app = FastAPI()
TK = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
GK = "AQ.Ab8RN6Kpct7KHJYWnDMp" + "QO9EWqEsN1886rewawWKYqMG-wS7Pg"
API = f"https://api.telegram.org/bot{TK}"
BG = "1000344641-93003ba8ae050194.jpg"

def get_bg():
    for f in [BG] + glob.glob("*.jpg") + glob.glob("*.png"):
        if os.path.exists(f):
            return base64.b64encode(open(f, "rb").read()).decode()
    return ""

def ask_ai(txt="", aud=None):
    p = [{"text": "أنت نظام شركة وييفقايد. حول الطلب لمستند HTML داخلي فقط بدون markdown مع جدول <table> للفواتير."}]
    if aud:
        p.append({"inline_data": {"mime_type": "audio/ogg", "data": aud}})
    if txt:
        p.append({"text": txt})
    u = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GK}"
    try:
        r = requests.post(u, json={"contents": [{"parts": p}]}, timeout=20)
        if r.ok:
            t = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            return t.replace("```html", "").replace("```", "")
    except Exception:
        pass
    ps = "".join([f"<p>{x}</p>" for x in txt.split("\n") if x.strip()])
    return f"<div class='sub'>مستند رسمي - وييفقايد</div>{ps}"

def make_pdf(body):
    b64 = get_bg()
    img = f"<img class='bg' src='data:image/jpeg;base64,{b64}'/>" if b64 else ""
    dt = datetime.now().strftime("%Y/%m/%dم")
    st = (
        "<svg width='110' height='110' viewBox='0 0 120 120'>"
        "<circle cx='60' cy='60' r='54' fill='none' stroke='#0C564C' stroke-width='3'/>"
        "<text x='60' y='48' text-anchor='middle' fill='#0C564C' font-size='10' font-weight='bold'>شركة وييفقايد</text>"
        "<text x='60' y='66' text-anchor='middle' fill='#0C564C' font-size='9' font-weight='bold'>للأعمال الهندسية</text>"
        "<text x='60' y='84' text-anchor='middle' fill='#F5B800' font-size='9'
