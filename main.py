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
    p = [{"text": """أنت نظام شركة وييفقايد للأعمال الهندسية.
حول الطلب لمستند HTML داخلي فقط بدون markdown مع جدول <table> للفواتير."""}]
    if aud:
        p.append({"inline_data": {"mime_type": "audio/ogg", "data": aud}})
    if txt:
        p.append({"text": txt})
    u = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-2.0-flash:generateContent?key={GK}"
    )
    try:
        r = requests.post(u, json={"contents": [{"parts": p}]}, timeout=20)
        if r.ok:
            t = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            bk = "`" * 3
            return t.replace
