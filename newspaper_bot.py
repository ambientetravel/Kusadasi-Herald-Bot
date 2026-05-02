import os
import sys
import datetime
import requests

# --- 1. AUTH & CONFIG ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TG_CHAT_IDS = os.environ.get("TELEGRAM_CHAT_ID", "")  # comma-separated: "5174458639,@ftdd1"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_KEY or not TG_TOKEN or not TG_CHAT_IDS:
    print("FATAL: Missing GitHub Secrets (GEMINI_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID).")
    sys.exit(1)

# --- 2. CSS TEMPLATE (locked design — model only fills body content) ---
CSS_TEMPLATE = """<style>
:root{--paper:#faf6ea;--paper-dark:#efe8d0;--ink:#111;--ink-soft:#2a2520;--faded:#706a5e;--red:#d92020;--red-dark:#a81515;--green:#2d6a3a;--gold:#b8860b;--blue:#1e3a5f;}
*{box-sizing:border-box;margin:0;padding:0;}
html{-webkit-text-size-adjust:100%;}
body{background:linear-gradient(#3a2e24,#1a1612);font-family:'Vazirmatn','Noto Naskh Arabic',Tahoma,sans-serif;color:var(--ink);direction:rtl;padding:16px 8px;min-height:100vh;line-height:1.75;}
.paper{max-width:540px;margin:0 auto;background:var(--paper);padding:22px 24px 36px;box-shadow:0 6px 24px rgba(0,0,0,0.4);background-image:radial-gradient(rgba(0,0,0,0.018) 1px,transparent 1px),radial-gradient(rgba(0,0,0,0.014) 1px,transparent 1px);background-size:18px 18px,11px 11px;background-position:0 0,9px 9px;}
.masthead{border-bottom:4px double var(--ink);padding-bottom:10px;margin-bottom:12px;}
.top-line{display:flex;justify-content:space-between;font-size:10px;letter-spacing:0.3px;color:var(--faded);padding-bottom:6px;border-bottom:1px solid var(--paper-dark);}
.masthead-block{position:relative;text-align:center;padding:8px 0 4px;display:flex;align-items:flex-end;justify-content:center;gap:8px;}
.roozname-label{background:var(--red);color:#fff;font-weight:700;font-size:13px;padding:5px 10px;letter-spacing:0.5px;writing-mode:vertical-rl;transform:rotate(180deg);align-self:stretch;display:flex;align-items:center;justify-content:center;border-radius:2px;}
.masthead-logo{font-family:'Vazirmatn',sans-serif;font-size:60px;font-weight:900;color:var(--red);line-height:0.95;letter-spacing:-1.5px;text-shadow:1px 1px 0 rgba(0,0,0,0.06);}
.english-sub{text-align:center;font-family:'Amiri',serif;font-style:italic;font-size:11px;color:var(--faded);margin-top:3px;letter-spacing:0.5px;}
.date-strip{display:flex;justify-content:space-between;align-items:center;margin-top:8px;padding:6px 4px;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);font-size:11px;font-weight:600;}
.edition{background:var(--ink);color:var(--paper);padding:3px 10px;letter-spacing:0.5px;}
.issue{color:var(--faded);}
.teaser-bar{background:var(--paper-dark);padding:8px 10px;margin-bottom:14px;font-size:11px;line-height:1.7;border-right:3px solid var(--red);}
.teaser-bar strong{color:var(--red);font-weight:700;margin-left:4px;}
.article{margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--paper-dark);}
.article:last-child{border-bottom:none;}
.article-kicker{font-size:10px;font-weight:700;color:var(--red);letter-spacing:1px;margin-bottom:4px;}
.article h2.lead{font-size:24px;font-weight:800;color:var(--ink);line-height:1.3;margin-bottom:6px;}
.article h2.sub-lead{font-size:17px;font-weight:700;color:var(--ink);line-height:1.35;margin-bottom:5px;}
.article h3.deck{font-family:'Amiri',serif;font-size:13px;font-style:italic;color:var(--ink-soft);font-weight:400;line-height:1.6;margin-bottom:10px;}
.byline-row{display:flex;align-items:center;gap:6px;font-size:10px;color:var(--faded);padding:6px 0;border-top:1px solid var(--paper-dark);border-bottom:1px solid var(--paper-dark);margin-bottom:10px;flex-wrap:wrap;}
.byline-row .headshot{width:22px;height:22px;background:var(--red);color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:11px;}
.byline-row .name{font-weight:700;color:var(--ink);}
.article p{font-size:13.5px;line-height:1.85;text-align:justify;margin-bottom:8px;color:var(--ink-soft);}
.article p .drop{font-size:28px;font-weight:800;color:var(--red);float:right;line-height:0.9;margin:4px 0 0 6px;font-family:'Amiri',serif;}
blockquote{margin:10px 0;padding:8px 12px;border-right:3px solid var(--red);background:var(--paper-dark);font-family:'Amiri',serif;font-style:italic;font-size:13px;color:var(--ink-soft);}
.section-header{background:var(--ink);color:var(--paper);padding:6px 10px;margin:18px 0 12px;font-size:12px;font-weight:700;letter-spacing:1px;text-align:center;}
.section-header::before,.section-header::after{content:"\\2605";margin:0 6px;color:var(--red);}
.section-header.red{background:var(--red);}
.section-header.blue{background:var(--blue);}
.section-header.green{background:var(--green);}
.section-header.gold{background:var(--gold);color:var(--ink);}
.box{background:#fff;border:1px solid var(--paper-dark);padding:10px 12px;margin:12px 0;font-size:12px;line-height:1.75;}
.box-title{font-weight:800;color:var(--red);font-size:13px;margin-bottom:6px;padding-bottom:4px;border-bottom:1px dashed var(--paper-dark);}
.box-row{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px dotted #e5e0d0;font-size:12px;}
.box-row:last-child{border-bottom:none;}
.box-row .value{font-weight:700;}
.up{color:var(--red);}
.down{color:var(--green);}
.same{color:var(--faded);}
.weather-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin:12px 0;}
.weather-cell{background:linear-gradient(180deg,#fff,var(--paper-dark));border:1px solid var(--paper-dark);padding:8px 4px;text-align:center;font-size:11px;}
.weather-cell .day{font-weight:700;color:var(--red);font-size:11px;margin-bottom:3px;}
.weather-cell .temp{font-size:18px;font-weight:800;color:var(--ink);}
.weather-cell .cond{font-size:10px;color:var(--faded);margin-top:2px;}
.city-weather{display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;margin:8px 0;}
.city-weather .cell{background:var(--paper-dark);padding:6px 4px;text-align:center;font-size:11px;}
.city-weather .city-name{font-weight:700;color:var(--red);font-size:10px;}
.city-weather .city-temp{font-size:16px;font-weight:800;}
.recipe-box{background:#fff;border:2px solid var(--green);padding:12px 14px;margin:14px 0;}
.recipe-title{font-size:17px;font-weight:800;color:var(--green);text-align:center;margin-bottom:4px;padding-bottom:6px;border-bottom:2px dashed var(--green);}
.recipe-heading{font-weight:800;color:var(--green);margin-top:8px;margin-bottom:4px;font-size:13px;}
.recipe-text{font-size:12.5px;line-height:1.75;color:var(--ink-soft);}
.migros-box{background:#fff8e1;border:2px dashed var(--gold);padding:10px 12px;margin:14px 0;}
.migros-title{text-align:center;font-weight:800;color:var(--gold);font-size:14px;margin-bottom:8px;padding-bottom:4px;border-bottom:1px dotted var(--gold);}
.migros-item{display:flex;justify-content:space-between;padding:4px 0;font-size:12px;border-bottom:1px dotted #e5d8a5;}
.migros-item:last-child{border-bottom:none;}
.migros-total{margin-top:6px;padding-top:6px;border-top:2px solid var(--gold);display:flex;justify-content:space-between;font-weight:800;color:var(--gold);font-size:13px;}
.health-tip{background:linear-gradient(135deg,#f0f7ee,#e0eee4);border-right:4px solid var(--green);padding:10px 12px;margin:12px 0;}
.health-title{font-weight:800;color:var(--green);font-size:13px;margin-bottom:4px;}
.health-text{font-size:12px;line-height:1.7;color:var(--ink-soft);}
.turkish-word{background:linear-gradient(135deg,#fff5f5,#ffe8e8);border:1px solid var(--red);padding:10px 12px;margin:12px 0;text-align:center;}
.turkish-title{font-size:11px;color:var(--red);font-weight:700;margin-bottom:4px;}
.turkish-main{font-size:22px;font-weight:800;color:var(--ink);margin:4px 0;}
.turkish-meaning{font-size:13px;color:var(--ink-soft);}
.turkish-ex{font-size:11px;font-style:italic;color:var(--faded);margin-top:4px;}
.history-box{background:#f5f0e0;border-right:3px solid var(--gold);padding:10px 12px;margin:12px 0;font-size:12px;}
.history-title{font-weight:800;color:var(--gold);font-size:13px;margin-bottom:6px;}
.history-item{padding:4px 0;border-bottom:1px dotted #e5d8a5;line-height:1.7;}
.history-item:last-child{border-bottom:none;}
.history-year{font-weight:800;color:var(--red);margin-left:6px;}
.closing{margin-top:22px;padding:14px 12px;background:linear-gradient(135deg,var(--red),var(--red-dark));color:#fff;text-align:center;border-radius:4px;}
.closing-title{font-size:16px;font-weight:800;margin-bottom:6px;}
.closing-text{font-size:12px;line-height:1.8;font-family:'Amiri',serif;font-style:italic;}
.footer{margin-top:18px;padding-top:10px;border-top:3px double var(--ink);text-align:center;font-size:9px;color:var(--faded);line-height:1.7;}
.footer .colophon{font-family:'Amiri',serif;font-style:italic;margin:6px 0;}
</style>"""

HEAD_FONTS = '''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800;900&family=Amiri:ital,wght@0,400;0,700;1,400;1,700&family=Noto+Naskh+Arabic:wght@400;500;600;700&display=swap" rel="stylesheet">'''


# --- 3. TIMING ---
now = datetime.datetime.now(datetime.timezone.utc)
local_hour = (now.hour + 3) % 24  # Kusadasi is UTC+3
is_morning = 7 <= local_hour <= 14
edition_en = "Morning" if is_morning else "Evening"
edition_fa = "بامداد" if is_morning else "عصر"
today_str = now.strftime("%Y-%m-%d")
today_human_en = now.strftime("%A, %d %B %Y")


# --- 4. PROMPT (Persian editorial brief) ---
PROMPT = f"""شما سردبیر ارشد روزنامه «کوشاداسی هرالد سان» هستید — یک روزنامه فارسی‌زبان روزانه برای جامعه فارسی‌زبان در کوشاداسی (سواحل اژه ترکیه) و خارج از کشور.

تاریخ امروز میلادی: {today_human_en} ({today_str})
نوبت انتشار: {edition_fa} ({edition_en})

== دستورالعمل کلیدی ==
از Google Search برای یافتن اخبار واقعی و امروزی استفاده کنید. اخبار جعلی ننویسید — فقط آنچه از نتایج جستجو تأیید شده. منابع اولویت‌دار:
1. بی‌بی‌سی فارسی (bbc.com/persian)
2. صدای آمریکا فارسی / ایران اینترنشنال
3. یورونیوز (euronews.com)
4. رسانه‌های معتبر داخل ایران (در صورت دقیق بودن)
5. اخبار محلی ترکیه (آیدین، کوشاداسی، Hürriyet، Habertürk)
6. اخبار ورزشی ایران (وارزش، طرفداری، فدراسیون فوتبال)
7. سوپر لیگ ترکیه (Turkish Süper Lig)
8. اخبار ایتالیا (رم) و اسپانیا (بارسلونا)

== الزامات خروجی ==
- فقط HTML خام تولید کنید (بدون ```html یا توضیح اضافی، با <!DOCTYPE html> شروع و با </html> پایان).
- زبان فارسی، چینش راست-به-چپ.
- <title>: «روزنامه کوشاداسی هرالد سان — {edition_fa} {today_str}»
- لوگوی ماست‌هد: «کوشاداسی هرالد سان»
- زیرعنوان انگلیسی: «— The Kusadasi Herald Sun · Persian {edition_en} Edition —»
- هیچ ایمیل، آدرس وب‌سایت، یا «info@» یا «https://» در footer نگنجانید.
- در footer فقط فهرست منابع استفاده‌شده + جمله‌ای کوتاه + تاریخ شماره بعدی.

== بخش‌ها به ترتیب ==
1. ماست‌هد (با date strip و شماره)
2. Teaser bar — ۴ تا ۶ تیتر مهم این شماره
3. «گزارش جهانی · ایران» (section-header red) — ۲ تا ۳ مقاله از منابع فارسی‌زبان (بی‌بی‌سی فارسی، VOA، یورونیوز)
4. «ورزش ایران» (section-header gold) — ۱ تا ۲ مقاله (تیم ملی فوتبال، لیگ برتر، کشتی، والیبال، یا ورزشکاران ایرانی)
5. «کوشاداسی · محلی» (section-header) — ۲ مقاله محلی (توریسم، بندر، رویدادهای آیدین/کوشاداسی)
6. «ورزش محلی · ترکیه» (section-header gold) — ۱ مقاله از Turkish Süper Lig یا ورزش منطقه آیدین
7. «گزارش از رم» (section-header blue) — ۱ مقاله از رم/ایتالیا
8. «بارسلونا · اسپانیا» (section-header green) — ۱ مقاله (FC Barcelona ترجیح دارد)
9. «بازار سوکه» (box) — قیمت نان، گوشت، پنیر گوسفندی، گوجه، شیر، با فلش‌های ↑ ↓ ⟷
10. «نرخ ارز» (box) — USD/TRY، EUR/TRY، USD/تومان، یورو/تومان، نفت برنت
11. «آب و هوا» (section-header blue) — weather-grid سه روز کوشاداسی + city-weather سه شهر (کوشاداسی، رم، بارسلونا)
12. «کلمه ترکی روز» (turkish-word) — یک کلمه/عبارت ترکی روزمره با ترجمه فارسی و مثال
13. «در چنین روزی» (history-box) — ۳ رویداد تاریخی این روز
14. «نکته بهداشتی» (health-tip) — مناسب سن ۷۰+
15. «آشپزی · دستور روز» (recipe-box) — یک دستور غذای ساده ایرانی، ترکی یا مدیترانه‌ای
16. «سبد خرید میگروس» (migros-box) — مواد لازم دستور بالا با قیمت‌های امروز و جمع کل
17. «closing» — پیام پایانی کوتاه و گرم
18. «footer» — فهرست منابع، colophon، تاریخ شماره بعدی. هیچ ایمیل/وب‌سایت/تماس.

== الگوی CSS (عیناً در <head> قرار دهید) ==
{CSS_TEMPLATE}

== فونت‌ها (در <head> قرار دهید قبل از <style>) ==
{HEAD_FONTS}

== ساختار body (محتوای واقعی را پر کنید، کلاس‌ها را تغییر ندهید) ==
<body>
<div class="paper">
  <div class="masthead">
    <div class="top-line"><span>کوشاداسی · ساحل اژه · رم · بارسلونا</span><span>★ شماره [N] · سال یکم</span></div>
    <div class="masthead-block">
      <div class="roozname-label">روزنامه</div>
      <div class="masthead-logo">کوشاداسی هرالد سان</div>
    </div>
    <div class="english-sub">— The Kusadasi Herald Sun · Persian {edition_en} Edition —</div>
    <div class="date-strip">
      <span class="edition">{edition_fa}</span>
      <span>[تاریخ شمسی فارسی]</span>
      <span class="issue">{today_str}</span>
    </div>
  </div>
  <div class="teaser-bar"><strong>◂ در این شماره ◂</strong> [4-6 تیتر جداشده با ·]</div>
  [section-header red] [مقالات ایران/جهان]
  [section-header gold] [ورزش ایران]
  [section-header] [کوشاداسی محلی]
  [section-header gold] [ورزش محلی ترکیه]
  [section-header blue] [رم]
  [section-header green] [بارسلونا]
  [section-header] [بازار سوکه + نرخ ارز]
  [section-header blue] [آب و هوا]
  [turkish-word]
  [history-box]
  [health-tip]
  [section-header green] [دستور آشپزی]
  [migros-box]
  [closing]
  [footer]
</div>
</body>

اکنون کل HTML را تولید کنید."""


# --- 5. GEMINI CALL (with Google Search grounding) ---
def generate(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"maxOutputTokens": 32000, "temperature": 0.7}
    }
    r = requests.post(url, headers=headers, json=payload, timeout=240)
    if r.status_code != 200:
        # Fallback: retry without search grounding if the tool isn't available
        if "google_search" in r.text or "tool" in r.text.lower():
            print("⚠️  Search grounding unavailable, retrying without it...")
            payload.pop("tools", None)
            r = requests.post(url, headers=headers, json=payload, timeout=240)
        if r.status_code != 200:
            raise Exception(f"Google API Error: {r.status_code} - {r.text}")
    data = r.json()
    return data['candidates'][0]['content']['parts'][0]['text']


# --- 6. TELEGRAM (multi-target) ---
def send_telegram(file_path, caption, chat_id):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    with open(file_path, 'rb') as doc:
        return requests.post(
            url,
            data={'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'},
            files={'document': (os.path.basename(file_path), doc, 'text/html')},
            timeout=120
        ).json()


# --- 7. MAIN ---
print(f"🚀 Generating {edition_en} edition for {today_str} via {MODEL}...")

try:
    html = generate(PROMPT)
except Exception as e:
    print(f"🛑 Generation failed: {e}")
    sys.exit(1)

# Strip markdown fences if the model disregards instructions
if "```html" in html:
    html = html.split("```html", 1)[1].rsplit("```", 1)[0].strip()
elif html.lstrip().startswith("```"):
    html = html.split("```", 1)[1].rsplit("```", 1)[0].strip()

filename = f"kusadasi-herald-sun-{edition_en.lower()}-{today_str}.html"
with open(filename, "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅ Saved {filename} ({len(html):,} chars)")

# Deliver to every chat ID in the secret (comma-separated)
caption = f"📰 <b>Kusadasi Herald Sun — {edition_en}</b>\n🗓 {today_str}"
chat_ids = [c.strip() for c in TG_CHAT_IDS.split(",") if c.strip()]
any_success = False
for chat_id in chat_ids:
    try:
        res = send_telegram(filename, caption, chat_id)
        if res.get("ok"):
            print(f"  ✓ Telegram → {chat_id}")
            any_success = True
        else:
            print(f"  ✗ Telegram → {chat_id}: {res}")
    except Exception as e:
        print(f"  ✗ Telegram → {chat_id}: {e}")

if not any_success:
    print("🛑 No deliveries succeeded.")
    sys.exit(1)

print("🎉 Done.")
