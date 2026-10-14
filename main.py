import base64, glob, io, os, requests
from datetime import datetime
from fastapi import FastAPI, Request
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

def build_body(txt):
    u = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/gemini-2.0-flash:generateContent?key={GK}"
    )
    pr = (
        "أنت نظام شركة وييفقايد للأعمال الهندسية. "
        "حول الطلب لمستند HTML داخلي فقط مع جدول <table> للفواتير."
    )
    try:
        pl = {"contents": [{"parts": [{"text": pr}, {"text": txt}]}]}
        r = requests.post(u, json=pl, timeout=20)
        if r.ok:
            res = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            bk = chr(96) * 3
            return res.replace(bk + "html", "").replace(bk, "")
    except Exception:
        pass
    lines = [x.strip() for x in txt.split("\n") if x.strip()]
    head = lines[0] if lines else "مستند رسمي"
    rest = lines[1:] if len(lines) > 1 else lines
    ps = "".join([f"<p>{x}</p>" for x in rest])
    return f"<div class='sub'>الموضوع / {head}</div>{ps}"

def make_pdf(txt):
    b64 = get_bg()
    img = f"<img class='bg' src='data:image/jpeg;base64,{b64}'/>" if b64 else ""
    dt = datetime.now().strftime("%Y/%m/%dم")
    body = build_body(txt)
    h = f"""<!DOCTYPE html><html dir='rtl'><head><meta charset='utf-8'><style>
@page {{ size: A4; margin: 0; }}
body {{
  font-family: 'Noto Sans Arabic', sans-serif;
  margin: 0; padding: 165px 50px 120px 50px;
  direction: rtl; font-size: 14px; line-height: 1.8;
}}
.bg {{ position: fixed; top: 0; left: 0; width: 210mm; height: 297mm; z-index: -9; }}
.bsm {{ text-align: center; font-weight: bold; margin-bottom: 10px; }}
.dt {{ font-weight: bold; color: #0C564C; margin-bottom: 15px; }}
.sub {{
  text-align: center; font-size: 17px; font-weight: bold;
  color: #0C564C; text-decoration: underline; margin: 15px 0;
}}
p {{ text-align: justify; margin: 8px 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: #fff; }}
th {{
  background: #0C564C; color: #fff; padding: 8px;
  border: 1px solid #0C564C; border-bottom: 3px solid #F5B800;
}}
td {{ padding: 8px; border: 1px solid #ccc; text-align: center; }}
.sig {{
  margin-top: 40px; text-align: left;
  padding-left: 25px; font-weight: bold; color: #0C564C;
}}
</style></head><body>
{img}
<div class='bsm'>بسم الله الرحمن الرحيم</div>
<div class='dt'>التاريخ: {dt}</div>
<div>{body}</div>
<div class='sig'>المدير العام<br>مهندس حسن طارق عامر بابكر</div>
</body></html>"""
    buf = io.BytesIO()
    HTML(string=h).write_pdf(buf)
    buf.seek(0)
    return buf

@app.get("/")
def home():
    return {"status": "Waveguide Active"}

@app.post("/webhook")
async def webhook(req: Request):
    d = await req.json()
    m = d.get("message", {})
    cid = m.get("chat", {}).get("id")
    txt = m.get("text", "").strip()
    if not cid or not txt:
        return {"ok": 1}
    if txt.startswith("/start"):
        requests.post(
            f"{API}/sendMessage",
            json={"chat_id": cid, "text": "مرحباً بك في نظام وييفقايد 📄"}
        )
        return {"ok": 1}
    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": cid, "text": "⏳ جاري إصدار المستند بالورقة المروّسة..."}
    )
    try:
        pdf = make_pdf(txt)
        files = {
            "document": ("Waveguide_Doc.pdf", pdf.getvalue(), "application/pdf")
        }
        requests.post(
            f"{API}/sendDocument",
            data={"chat_id": cid, "caption": "✅ تم الإصدار بنجاح"},
            files=files
        )
    except Exception as e:
        requests.post(
            f"{API}/sendMessage",
            json={"chat_id": cid, "text": f"⚠️ خطأ: {e}"}
        )
    return {"ok": 1}
