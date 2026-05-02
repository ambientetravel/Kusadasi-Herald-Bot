import os
import sys
import datetime
import requests
import json

# --- 1. AUTH & CONFIG ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_KEY, TG_TOKEN, TG_CHAT_ID]):
    print("FATAL: Missing GitHub Secrets.")
    sys.exit(1)

def generate_content_direct(prompt):
    # استفاده از آدرس مستقیم API برای دور زدن باگ‌های کتابخانه‌ای
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Google API Error: {response.status_code} - {response.text}")
    
    data = response.json()
    return data['candidates'][0]['content']['parts'][0]['text']

def send_to_telegram(file_path, caption):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as doc:
            payload = {'chat_id': TG_CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
            files = {'document': (os.path.basename(file_path), doc, 'text/html')}
            r = requests.post(url, data=payload, files=files)
            return r.json()
    except Exception as e:
        print(f"Telegram Failed: {e}")
        return None

# --- 2. LOGIC ---
now = datetime.datetime.now(datetime.timezone.utc)
is_morning = 4 <= now.hour <= 11 
edition = "Morning" if is_morning else "Evening"
today_str = now.strftime("%Y-%m-%d")

prompt = f"""
Act as the Senior Editor for 'Kusadasi Herald'. Output a professional Persian HTML newspaper for {edition} {today_str}.
Include: Kusadasi news, Port Cruises, Weather, Iran/Washington news, Rome/Barcelona news.
Output ONLY raw HTML. No markdown tags.
"""

print(f"🚀 Direct API Call for {edition} edition...")

try:
    html_body = generate_content_direct(prompt)
    
    # Cleanup any markdown if AI ignores the instruction
    if "```html" in html_body:
        html_body = html_body.split("```html")[1].split("```")[0].strip()
    elif "```" in html_body:
        html_body = html_body.split("```")[1].split("```")[0].strip()

    filename = f"Kusadasi_Herald_{today_str}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_body)

    status = send_to_telegram(filename, f"📰 <b>Kusadasi Herald: {edition}</b>\n🗓 {today_str}")
    
    if status and status.get("ok"):
        print("🎉 Delivered successfully via Direct API!")
    else:
        print(f"⚠️ Telegram error: {status}")
        sys.exit(1)

except Exception as e:
    print(f"🛑 Critical Error: {e}")
    sys.exit(1)
