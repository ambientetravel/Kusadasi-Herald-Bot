import google.generativeai as genai
import datetime
import requests
import os

# Securely fetch keys from GitHub Actions Secrets
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def send_to_telegram(file_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    with open(file_path, 'rb') as file:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
        files = [('document', (os.path.basename(file_path), file, 'text/html'))]
        return requests.post(url, data=payload, files=files).json()

# Logic to determine edition based on Server Time (UTC)
now_hour = datetime.datetime.utcnow().hour
if 5 <= now_hour <= 10:
    edition = "Morning (10:00 AM)"
else:
    edition = "Evening (21:30 PM)"

today = datetime.datetime.now().strftime("%Y-%m-%d")
weekday = datetime.datetime.now().weekday() # 4 is Friday

# Recipe Rotation Logic
recipe_types = ["Persian", "Turkish", "Persian", "Turkish", "Spanish", "Italian", "Persian"]
today_recipe = recipe_types[weekday]

prompt = f"""
Act as the Senior Editor of 'Kusadasi Herald'. Generate a high-end Persian HTML newspaper for the {edition}.

CONTENT STRUCTURE:
1. LOCAL HUB: News for Kusadasi, Unique Residence, Söke, markets, and events for the next 7 days. 
   - List today's Cruise Ships in the Port of Kusadasi.
   - Weather: TODAY (Yellow/Bold background), Tomorrow & Day After (Mild colors). 
   - Include current temperature for Rome and Barcelona next to the weather section.

2. GLOBAL NEWS: 
   - 4 latest Iran news (focus on Washington-Iran relations). Pick one for a 'Story of the Day' long-form analysis.
   - Rome & Barcelona: 2 news each (1 Political, 1 Cultural) + upcoming major events.
   {"- FRIDAY SPECIAL: A full 'Wrap-up' of all celebrations/events for the next week in Kusadasi, Rome, and Barcelona." if weekday == 4 else ""}

3. TOURISM & PORT: Latest cruises in port and global tourism trends.

4. KITCHEN (Morning Only): Suggest a {today_recipe} dish. Include a full recipe and a Migros 'Shopping Basket' with estimated prices in TRY.

5. NIGHT CAP (Evening Only): A soothing summary of the day's events.

DESIGN: Use internal CSS. Corporate colors: Red, Green, Blue. Output ONLY the raw HTML code.
"""

response = model.generate_content(prompt)
    # This line ensures we only get the HTML content even if Gemini adds markdown tags
    html_content = response.text.replace("```html", "").replace("```", "").strip()

    file_name = f"Kusadasi_Herald_{today}_{edition.split()[0]}.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Send to Telegram
    result = send_to_telegram(file_name, f"📰 <b>Kusadasi Herald - {edition}</b>\n🗓 {today}")
    print("Telegram Response:", result)
except Exception as e:
    print(f"Error occurred: {e}")
    exit(1) # This tells GitHub the run failed if an error happens
