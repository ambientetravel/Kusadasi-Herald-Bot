import os
import sys
import time
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


# --- 4. HTML SHELL (Python owns this — CSS never goes through the model) ---
HTML_HEAD = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#d92020">
<title>روزنامه کوشاداسی هرالد سان — {edition_fa} {today_str}</title>
{HEAD_FONTS}
{CSS_TEMPLATE}
</head>
<body>
<div class="paper">
"""

HTML_TAIL = """
</div>
</body>
</html>"""


# --- 5. PROMPT (asks for inner content only — saves ~5K tokens of CSS regurgitation) ---
PROMPT = f"""شما سردبیر ارشد روزنامه «کوشاداسی هرالد سان» هستید — یک روزنامه فارسی‌زبان روزانه برای جامعه فارسی‌زبان در کوشاداسی (سواحل اژه ترکیه) و خارج از کشور.

تاریخ امروز میلادی: {today_human_en} ({today_str})
نوبت انتشار: {edition_fa} ({edition_en})

== دستورالعمل کلیدی ==
از Google Search برای یافتن اخبار واقعی و امروزی استفاده کنید. اخبار جعلی ننویسید — فقط آنچه از نتایج جستجو تأیید شده. منابع اولویت‌دار:
- بی‌بی‌سی فارسی، صدای آمریکا فارسی، ایران اینترنشنال، یورونیوز
- رسانه‌های معتبر داخل ایران (در صورت دقیق بودن)
- اخبار محلی ترکیه (Hürriyet، Habertürk، Aydın Post)
- ورزش ایران (طرفداری، وارزش، فدراسیون فوتبال) و Turkish Süper Lig
- اخبار ایتالیا (رم) و اسپانیا (بارسلونا — به‌ویژه FC Barcelona)

== خروجی — مهم ==
فقط HTML داخلی div.paper را تولید کنید. هیچ <!DOCTYPE>, <html>, <head>, <body>, <style>, <link>, <div class="paper">, و یا </div> پایانی ننویسید — Python آن‌ها را اضافه می‌کند.
فقط با <div class="masthead"> شروع کنید و با </div> پایانی footer به اتمام برسانید.
بدون ```html و بدون توضیح اضافی.

== ماست‌هد دقیقاً به این شکل ==
<div class="masthead">
  <div class="top-line"><span>کوشاداسی · ساحل اژه · رم · بارسلونا</span><span>★ شماره [N] · سال یکم</span></div>
  <div class="masthead-block">
    <div class="roozname-label">روزنامه</div>
    <div class="masthead-logo">کوشاداسی هرالد سان</div>
  </div>
  <div class="english-sub">— The Kusadasi Herald Sun · Persian {edition_en} Edition —</div>
  <div class="date-strip">
    <span class="edition">{edition_fa}</span>
    <span>[تاریخ شمسی فارسی این روز را بنویسید]</span>
    <span class="issue">{today_str}</span>
  </div>
</div>

== کلاس‌های مجاز CSS (دقیقاً همین‌ها را استفاده کنید) ==
.teaser-bar | .article | .article-kicker | h2.lead | h2.sub-lead | h3.deck | .byline-row > .headshot, .name | .drop | blockquote
.section-header (با variants .red .blue .green .gold)
.box | .box-title | .box-row > .label, .value | .up .down .same
.weather-grid > .weather-cell > .day .temp .cond
.city-weather > .cell > .city-name .city-temp
.turkish-word > .turkish-title .turkish-main .turkish-meaning .turkish-ex
.history-box > .history-title .history-item > .history-year
.health-tip > .health-title .health-text
.recipe-box > .recipe-title .recipe-heading .recipe-text
.migros-box > .migros-title .migros-item > .migros-name .migros-price | .migros-total
.closing > .closing-title .closing-text
.footer > .colophon

== بخش‌ها به ترتیب (با section-header مناسب قبل از هر بخش که عنوان دارد) ==
1. <div class="masthead">...</div>
2. <div class="teaser-bar"><strong>◂ در این شماره ◂</strong> ۴ تا ۶ تیتر · جداشده · با · نقطه‌های پررنگ</div>
3. section-header red «گزارش جهانی · ایران» — سپس ۲ تا ۳ <article class="article"> با kicker, h2.lead, h3.deck, byline-row, پاراگراف‌ها (یکی drop داشته باشد)، و یک blockquote با نقل‌قول از منبع.
4. section-header gold «ورزش ایران» — ۱ تا ۲ مقاله (فوتبال تیم ملی، لیگ برتر، کشتی، والیبال، ورزشکاران).
5. section-header (بدون رنگ) «کوشاداسی · محلی» — ۲ مقاله محلی (توریسم، بندر، رویدادهای آیدین).
6. section-header gold «ورزش محلی · ترکیه» — ۱ مقاله Süper Lig یا ورزش آیدین.
7. section-header blue «گزارش از رم» — ۱ مقاله.
8. section-header green «بارسلونا · اسپانیا» — ۱ مقاله (FC Barcelona ترجیح دارد).
9. section-header (بدون رنگ) «بازار سوکه» — یک div.box با قیمت‌های نان، گوشت گوساله، پنیر گوسفندی، گوجه، شیر، باقالا — هر row با .up/.down/.same.
10. div.box با عنوان «نرخ ارز» — USD/TRY، EUR/TRY، USD/تومان، EUR/تومان، نفت برنت.
11. section-header blue «آب و هوا» — div.box شامل weather-grid (۳ روز کوشاداسی) و city-weather (کوشاداسی، رم، بارسلونا).
12. div.turkish-word — یک عبارت ترکی روزمره با ترجمه فارسی و مثال.
13. div.history-box — ۳ رویداد تاریخی این روز (با history-year پررنگ).
14. div.health-tip — مناسب سن ۷۰+، مرتبط با هوای امروز یا فصل.
15. section-header green «آشپزی · دستور روز» — div.recipe-box با عنوان، اجزا، طرز تهیه، یک یادداشت سلامتی کوتاه.
16. div.migros-box — مواد لازم همان دستور با قیمت‌های امروز و جمع کل.
17. div.closing — پیام پایانی کوتاه و گرم با closing-title و closing-text.
18. div.footer — colophon، فهرست منابع امروز (مثلاً «منابع: BBC Persian · VOA · Euronews · Hürriyet · ...»)، تاریخ شماره بعدی. بدون ایمیل، بدون آدرس وب، بدون «info@» یا «https».

اکنون شروع کنید — اولین کاراکتر باید < باشد و آخرین کاراکتر باید > باشد. فقط HTML داخلی."""


# --- 5. GEMINI CALL (with Google Search grounding, robust to filtered/empty responses) ---
def _extract_text(data):
    """Pull text from Gemini response, tolerant of various response shapes."""
    candidates = data.get('candidates') or []
    if not candidates:
        block = data.get('promptFeedback', {}).get('blockReason')
        raise Exception(f"Gemini returned no candidates (blockReason={block!r}; full={data})")
    cand = candidates[0]
    finish = cand.get('finishReason', '')
    parts = (cand.get('content') or {}).get('parts') or []
    text_chunks = [p['text'] for p in parts if isinstance(p, dict) and 'text' in p]
    text = ''.join(text_chunks)
    if not text:
        raise Exception(
            f"Gemini returned empty text (finishReason={finish!r}, parts={len(parts)}, "
            f"safetyRatings={cand.get('safetyRatings')})"
        )
    if finish == 'MAX_TOKENS':
        print(f"⚠️  Gemini hit MAX_TOKENS — output may be truncated ({len(text):,} chars).")
    elif finish and finish != 'STOP':
        print(f"⚠️  Gemini finishReason: {finish} ({len(text):,} chars)")
    return text


TRANSIENT_HTTP = {429, 500, 502, 503, 504}


def _post_with_retry(url, payload, attempts=5, base_delay=20):
    """POST with exponential backoff on transient errors (rate limits, 503, etc.)."""
    last = None
    for i in range(attempts):
        last = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=240)
        if last.status_code == 200:
            return last
        if last.status_code not in TRANSIENT_HTTP:
            return last  # permanent error — don't waste retries
        if i < attempts - 1:
            delay = base_delay * (2 ** i)  # 20s, 40s, 80s, 160s
            print(f"   HTTP {last.status_code}, retrying in {delay}s ({i + 1}/{attempts})...")
            time.sleep(delay)
    return last


def generate(prompt):
    base_payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 60000, "temperature": 0.7}
    }
    # Try in this order: preferred model grounded → preferred ungrounded → fallback model ungrounded.
    # Each step gets its own retry loop with exponential backoff.
    fallback_model = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-2.5-pro")
    attempts = [
        (MODEL, True),
        (MODEL, False),
        (fallback_model, False),
    ]

    last_error = "(no attempt made)"
    for model, grounded in attempts:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
        payload = dict(base_payload)
        if grounded:
            payload["tools"] = [{"google_search": {}}]
        label = f"{model}{' + grounding' if grounded else ''}"
        print(f"   → Trying {label}...")

        r = _post_with_retry(url, payload)
        if r.status_code != 200:
            last_error = f"HTTP {r.status_code}: {r.text[:300]}"
            print(f"   ✗ {label}: {last_error}")
            continue
        try:
            return _extract_text(r.json())
        except Exception as e:
            last_error = str(e)
            print(f"   ✗ {label}: {last_error}")
            continue

    raise Exception(f"All Gemini attempts exhausted. Last error: {last_error}")


def extract_inner(model_output):
    """Strip markdown fences and any wrapping shell the model returns despite instructions."""
    s = model_output.strip()
    # Strip ```html ... ``` fences
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s[3:]
        if s.rstrip().endswith("```"):
            s = s.rsplit("```", 1)[0]
        s = s.strip()
    # If model returned a full doc, extract just the .paper inner content
    if "<div class=\"paper\"" in s:
        s = s.split("<div class=\"paper\"", 1)[1]
        s = s.split(">", 1)[1]  # past the opening tag's >
        # Find the matching closing </body> or </html> and trim everything from the last </div> before it
        for marker in ("</body>", "</html>"):
            if marker in s:
                s = s.split(marker, 1)[0]
        # Remove trailing closing div(s) that wrapped .paper
        s = s.rstrip()
        if s.endswith("</div>"):
            s = s[:-len("</div>")].rstrip()
    return s.strip()


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
    raw = generate(PROMPT)
except Exception as e:
    print(f"🛑 Generation failed: {e}")
    sys.exit(1)

inner = extract_inner(raw)
html = HTML_HEAD + inner + HTML_TAIL

filename = f"kusadasi-herald-sun-{edition_en.lower()}-{today_str}.html"
with open(filename, "w", encoding="utf-8") as f:
    f.write(html)
print(f"✅ Saved {filename} ({len(html):,} chars; model produced {len(inner):,} chars of body)")

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
