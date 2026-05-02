import os
import sys
import datetime
import requests
from google import genai

# --- 1. ENVIRONMENT & AUTHENTICATION ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_KEY, TG_TOKEN, TG_CHAT_ID]):
    print("FATAL: Missing GitHub Secrets. Check GEMINI_API_KEY, TELEGRAM_TOKEN, and TELEGRAM_CHAT_ID.")
    sys.exit(1)

# Initialize the modern 2026 GenAI Client
client = genai.Client(api_key=GEMINI_KEY)

def send_to_telegram(file_path, caption):
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TG_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as doc:
            payload = {'chat_id': TG_CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
            files = {'document': (os.path.basename(file_path), doc, 'text/html')}
            response = requests.post(url, data=payload, files=files)
            return response.json()
    except Exception as e:
        print(f"Telegram Upload Failed: {e}")
        return None

# --- 2. LOGIC FOR EDITIONS ---
# Using timezone-aware UTC for 2026 Python standards
now = datetime.datetime.now(datetime.timezone.utc)
# Adjusting for Turkey Time (UTC+3)
is_morning = 4 <= now.hour <= 11 
edition = "Morning (10:00 AM)" if is_morning else "Evening (21:30 PM)"
today_str = now.strftime("%Y-%m-%d")
weekday = now.weekday() # 4 is Friday

# Meal Rotation
recipe_map = ["Persian", "Turkish", "Persian", "Turkish", "Spanish", "Italian", "Persian"]
today_recipe = recipe_map[weekday]

# --- 3. THE EXPERT PROMPT ---
prompt = f"""
Act as the Senior Editor for 'Kusadasi Herald'. Output a high-end, professional Persian (Farsi) HTML newspaper.
EDITION: {edition} for {today_str}.

REQUIREMENTS:
1. LOCAL: Kusadasi news, Unique Residence updates, Söke events. Port of Kusadasi: Today's Cruises.
2. WEATHER: Kusadasi Today (Bold Highlight), Tomorrow & Day After (Subtle). Include Rome & Barcelona temps.
3. GLOBAL: 4 Iran news (Washington/Internal), 2 Rome, 2 Barcelona (1 Political, 1 Cultural). 
4. FRIDAY: If today is Friday, include a 'Week Ahead' wrap-up for all 3 cities.
5. KITCHEN: Suggest a {today_recipe} dish with Migros market shopping list.
6. DESIGN: Use internal CSS with Red, Green, and Blue corporate accents. 

IMPORTANT: Output ONLY valid HTML code. Do NOT include markdown backticks (```html) or introductory text.
"""

print(f"🚀 Initializing {edition} generation for {today_str}...")

try:
    # Using gemini-1.5-flash for speed and reliability in automation
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    
    # Clean output: Remove any potential AI-generated markdown wrappers
    html_body = response.text.strip()
    if html_body.startswith("```"):
        html_body = html_body.split("\n", 1)[-1].rsplit("\n", 1)[0]

    filename = f"Kusadasi_Herald_{today_str}_{'AM' if is_morning else 'PM'}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_body)

    print(f"✅ Success: {filename} generated. Delivering to Telegram...")
    
    status = send_to_telegram(filename, f"📰 <b>Kusadasi Herald: {edition}</b>\n🗓 {today_str}")
    
    if status and status.get("ok"):
        print("🏁 Mission Accomplished: Newspaper delivered.")
    else:
        print(f"⚠️ Telegram Delivery Failed: {status}")
        sys.exit(1)

except Exception as e:
    print(f"🛑 Critical Engine Failure: {e}")
    sys.exit(1)
