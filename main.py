import os
import io
import glob
import logging
from datetime import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from weasyprint import HTML

# ضبط سجل الأخطاء والمتابعة في منصة Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waveguide-bot")

app = FastAPI(title="Waveguide Bot Service")

# التوكن المعتمد الخاص بالبوت
BOT_TOKEN = "8730433601:AAEA2qHbPxtt1Z3-oWoQIBlFWNAjwe9NP04"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def get_letterhead_path():
    """البحث عن صورة الورقة المروّسة الرسمية داخل مجلد المشروع"""
    # فحص الأسماء المعتمدة أولاً
    candidates = [
        "waveguide-letterhead.png",
        "waveguide-letterhead.jpg",
        "letterhead.png",
        "letterhead.jpg",
    ]
    for filename in candidates:
        if os.path.exists(
