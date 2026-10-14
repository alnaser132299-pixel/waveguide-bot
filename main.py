import base64, glob, io, os, re, requests
from datetime import datetime
from fastapi import FastAPI, Request
from weasyprint import HTML

app = FastAPI()
TK = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
API = f"https://api.telegram.org/bot{TK}"
BG = "1000344641-93003ba8ae050194.jpg"

def get_bg():
    for f in [BG] + glob.glob("*.jpg") + glob.glob("*.png"):
        if os.path.exists(f):
            return base64.b64encode(open(f, "rb").read()).decode()
    return ""

def build_body(txt):
    lines = [x.strip() for x in txt.split("\n") if x.strip()]
    if not lines:
        return "<p></p>"
    first = lines[0]

    if any(k in first for k in ["فاتورة", "عرض سعر", "مستخلص", "مقايسة"]):
        rows = ""
        tot = 0
        idx = 1
        notes = []
        for ln in lines[1:]:
            pts = [p.strip() for p in re.split(r"[-/|،,]", ln) if p.strip()]
            nums = []
            for p in pts:
                cl = re.sub(r"[^\d.]", "", p)
                if cl and not re.search(r"[أ-يa-zA-Z]", p):
                    nums.append(float(cl))
            if len(pts) >= 2 and len(nums) >= 1:
                name = pts[0]
                qty = nums[0] if len(nums) >= 2 else 1
                prc = nums[1] if len(nums) >= 2 else nums[0]
                sub = qty * prc
                tot += sub
                qs = int(qty) if qty.is_integer() else qty
                rows += f"""<tr>
                  <td>{idx}</td>
                  <td style='text-align:right;font-weight:bold;'>{name}</td>
                  <td>{qs}</td>
                  <td>{prc:,.0f}</td>
                  <td style='font-weight:bold;'>{sub:,.0f}</td>
                </tr>"""
                idx += 1
            else:
                notes.append(f"<p>{ln}</p>")
        ext = "".join(notes)
        return f"""
        <div class='sub'>{first}</div>
        {ext}
        <table>
          <thead>
            <tr>
              <th style='width:8%;'>م</th>
              <th style='width:46%;'>البيان / وصف الأعمال</th>
              <th style='width:12%;'>الكمية</th>
              <th style='width:17%;'>سعر الوحدة</th>
              <th style='width:17%;'>الإجمالي</th>
            </tr>
          </thead>
          <tbody>
            {rows}
            <tr class='tot'>
              <td colspan='4'>الإجمالي الكلي (TOTAL)</td>
              <td>{tot:,.0f}</td>
            </tr>
          </tbody>
        </table>"""

    if any(first.startswith(w) for w in ["السادة", "إلى", "الأخوة"]):
        to_l = first
        sub = lines[1] if len(lines) > 1 else "موضوع رسمي"
        sub = sub.replace("الموضوع:", "").replace("الموضوع /", "").strip()
        ps = "".join([f"<p>{x}</p>" for x in lines[2:]])
        return f"""
        <div class='to'>{to_l}</div>
        <div class='gr'>السلام عليكم ورحمة الله تعالى وبركاته،،،</div>
        <div class='sub'>الموضوع / {sub}</div>
        {ps}
        <div class='end'>ولسيادتكم وافر الشكر والتقدير،،،</div>"""

    ps = "".join([f"<p>{x}</p>" for x in lines[1:]])
    return f"<div class='sub'>الموضوع / {first}</div>{ps}"

def make_pdf(txt):
    b64 = get_bg()
    img = f"<img class='bg' src='data:image/jpeg;base64,{b64}'/>" if b64 else ""
    dt = datetime.now().strftime("%Y/%m/%dم")
    body = build_body(txt)
    h = f"""<!DOCTYPE html><html dir='rtl'><head><meta charset='utf-8'><style>
@page {{ size: A4; margin: 0; }}
body {{
  font-family: 'Noto Sans Arabic', sans-serif;
  margin: 0; padding: 160px 50px 120px 50px;
  direction: rtl; font-size: 14px; line-height: 1.8; color: #111;
}}
.bg {{ position: fixed; top: 0; left: 0; width: 210mm; height: 297mm; z-index: -9; }}
.bsm {{ text-align: center; font-weight: bold; margin-bottom: 8px; }}
.dt {{ font-weight: bold; color: #0C564C; margin-bottom: 12px; }}
.to {{ font-weight: bold; font-size: 15px; margin-bottom: 6px; }}
.gr {{ font-weight: bold; margin-bottom: 12px; }}
.sub {{
  text-align: center; font-size: 16.5px; font-weight: bold;
  color: #0C564C; text-decoration: underline; margin: 14px 0;
}}
p {{ text-align: justify; margin: 8px 0; }}
.end {{ text-align: center; font-weight: bold; margin-top: 18px; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: #fff; }}
th {{
  background: #0C564C; color: #fff; padding: 8px;
  border: 1px solid #0C564C; border-bottom: 3px solid #F5B800; font-size: 13px;
}}
td {{ padding: 8px; border: 1px solid #cbd5e1; text-align: center; font-size: 13.5px; }}
.tot td {{
  background: #f1f5f9; font-weight: bold; color: #0C564C;
  border-bottom: 3px double #0C564C; font-size: 14.5px;
}}
.sig {{ margin-top: 25px; text-align: left; padding-left: 15px; }}
.sig-in {{
  display: inline-block; text-align: center;
  font-weight: bold; color: #0C564C; position: relative;
}}
.stamp-box {{
  width: 118px; height: 118px; margin: 6px auto 0 auto;
  border: 3.5px double #0C564C; border-radius: 50%;
  padding-top: 16px; box-sizing: border-box;
  transform: rotate(-7deg); color: #0C564C;
  background: rgba(12, 86, 76, 0.03);
}}
.st-1 {{ font-size: 10.5px; font-weight: bold; line-height: 1.3; }}
.st-2 {{
  font-size: 9px; font-weight: bold; color: #b48600;
  border-top: 1px solid #F5B800; border-bottom: 1px solid #F5B800;
  margin: 3px 10px; padding: 1px 0;
}}
.st-3 {{ font-size: 8.5px; line-height: 1.2; }}
.pen-sig {{ margin-top: -42px; position: relative; z-index: 5; }}
</style></head><body>
{img}
<div class='bsm'>بسم الله الرحمن الرحيم</div>
<div class='dt'>التاريخ: {dt}</div>
<div>{body}</div>
<div class='sig'><div class='sig-in'>
  المدير العام<br>مهندس حسن طارق عامر بابكر
  <div class='stamp-box'>
    <div class='st-1'>شركة وييفقايد<br>للأعمال الهندسية</div>
    <div class='st-2'>WAVEGUIDE ENG</div>
    <div class='st-3'>الإدارة العامة - معتمد</div>
  </div>
  <div class='pen-sig'>
    <svg xmlns='http://www.w3.org/2000/svg' width='130' height='45' viewBox='0 0 150 50'>
      <path d='M 20 35 Q 45 5 60 30 T 105 18 Q 125 12 135 28 M 35 28 L 115 22'
            fill='none' stroke='#0a3d62' stroke-width='2.4' stroke-linecap='round'/>
    </svg>
  </div>
</div></div>
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
        msg = (
            "مرحباً بك في نظام وييفقايد 📄\n"
            "أرسل تفاصيل الفاتورة أو الخطاب لإصدار الـ PDF فوراً."
        )
        requests.post(f"{API}/sendMessage", json={"chat_id": cid, "text": msg})
        return {"ok": 1}
    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": cid, "text": "⏳ جاري إعداد المستند المروّس مع الختم..."}
    )
    try:
        pdf = make_pdf(txt)
        files = {
            "document": ("Waveguide_Doc.pdf", pdf.getvalue(), "application/pdf")
        }
        requests.post(
            f"{API}/sendDocument",
            data={"chat_id": cid, "caption": "✅ تم الإصدار بالختم والتوقيع"},
            files=files
        )
    except Exception as e:
        requests.post(
            f"{API}/sendMessage",
            json={"chat_id": cid, "text": f"⚠️ خطأ: {e}"}
        )
    return {"ok": 1}
