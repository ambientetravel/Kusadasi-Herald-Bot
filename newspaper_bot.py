import google.generativeai as genai
import datetime
import requests
import os
import sys

# Fetch keys from GitHub Secrets
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
    print("❌ Error: Missing GitHub Secrets!")
    sys.exit(1)

genai.configure(api_key=GEMINI_KEY)
# تغییر نام مدل به نسخه پایدار و جدید
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def send_to_telegram(file_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as file:
            payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
            files = [('document', (os.path.basename(file_path), file, 'text/html'))]
            response = requests.post(url, data=payload, files=files)
            return response.json()
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return None

now_hour = datetime.datetime.utcnow().hour
edition = "Morning (10:00 AM)" if 5 <= now_hour <= 12 else "Evening (21:30 PM)"
today = datetime.datetime.now().strftime("%Y-%m-%d")
weekday = datetime.datetime.now().weekday()

recipe_types = ["Persian", "Turkish", "Persian", "Turkish", "Spanish", "Italian", "Persian"]
today_recipe = recipe_types[weekday]

prompt = f"""
Act as the Senior Editor of 'Kusadasi Herald'. Generate a high-end Persian HTML newspaper for the {edition}.
Local news: Kusadasi, Unique Residence, Soke, Port Cruises, Weather for Kusadasi, Rome, Barcelona.
Global: 4 Iran news (Washington focus), 2 Rome, 2 Barcelona news.
Kitchen: {today_recipe} dish with Migros basket.
Output ONLY the raw HTML code without markdown tags.
"""

print(f"⏳ Generating {edition} for {today}...")

try:
    response = model.generate_content(prompt)
    # پاکسازی متن از هرگونه علامت اضافی مارک‌داون
    raw_text = response.text
    html_content = raw_text.replace("```html", "").replace("```", "").strip()

    file_name = f"Kusadasi_Herald_{today}_{edition.split()[0]}.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ File {file_name} created. Sending to Telegram...")
    status = send_to_telegram(file_name, f"📰 <b>Kusadasi Herald - {edition}</b>\n🗓 {today}")
    
    if status and status.get("ok"):
        print("🎉 Success! Newspaper delivered.")
    else:
        print(f"❌ Telegram Failed: {status}")
        sys.exit(1)
except Exception as e:
    print(f"💥 Critical Crash: {e}")
    sys.exit(1)
