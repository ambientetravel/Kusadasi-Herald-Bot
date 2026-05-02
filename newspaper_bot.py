import os
import sys
import datetime
import requests
from google import genai

# --- 1. AUTHENTICATION ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_KEY, TG_TOKEN, TG_CHAT_ID]):
    print("FATAL: Missing GitHub Secrets.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_KEY)

def send_to_telegram(file_path, caption):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as doc:
            payload = {'chat_id': TG_CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
            files = {'document': (os.path.basename(file_path), doc, 'text/html')}
            response = requests.post(url, data=payload, files=files)
            return response.json()
    except Exception as e:
        print(f"Telegram Upload Failed: {e}")
        return None

# --- 2. LOGIC ---
now = datetime.datetime.now(datetime.timezone.utc)
is_morning = 4 <= now.hour <= 11 
edition = "Morning (10:00 AM)" if is_morning else "Evening (21:30 PM)"
today_str = now.strftime("%Y-%m-%d")
weekday = now.weekday()

recipe_map = ["Persian", "Turkish", "Persian", "Turkish", "Spanish", "Italian", "Persian"]
today_recipe = recipe_map[weekday]

prompt = f"""
Act as the Senior Editor for 'Kusadasi Herald'. Output a high-end professional Persian HTML newspaper.
EDITION: {edition} for {today_str}.
Kusadasi local news, Cruises, Weather (Kusadasi, Rome, Barcelona), Iran news (Washington focus), 
2 Rome news, 2 Barcelona news. Recipe: {today_recipe}.
Output ONLY raw HTML code. No markdown.
"""

print(f"🚀 Attempting to generate {edition} using Gemini 1.5 Flash...")

try:
    # اصلاح نام مدل به ساده‌ترین حالت برای جلوگیری از خطای 404
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents=prompt
    )
    
    html_body = response.text.strip()
    # حذف هرگونه تگ مارک‌داون احتمالی
    if "```html" in html_body:
        html_body = html_body.split("```html")[1].split("```")[0].strip()
    elif "```" in html_body:
        html_body = html_body.split("```")[1].split("```")[0].strip()

    filename = f"Kusadasi_Herald_{today_str}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_body)

    status = send_to_telegram(filename, f"📰 <b>Kusadasi Herald: {edition}</b>\n🗓 {today_str}")
    
    if status and status.get("ok"):
        print("🎉 Delivered successfully!")
    else:
        print(f"⚠️ Telegram error: {status}")
        sys.exit(1)

except Exception as e:
    print(f"🛑 Engine Failure: {e}")
    sys.exit(1)
