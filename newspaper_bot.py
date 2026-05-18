import os
import re
import sys
import time
import datetime
import html as htmllib
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


# --- 3b. MEMORIAL CALENDAR (recurring anniversaries — switch to mourning edition) ---
# On these dates each year, the newspaper takes a memorial form: muted palette,
# a banner above the masthead, a Khayyam quatrain, and the loved one's name.
MEMORIAL_DATES = {
    # Format: 'MM-DD' → memorial details
    '05-15': {
        'name_fa':       'جهانگیر نوریشاد',
        'name_en':       'Jahangir Nourishad',
        # Poetic descriptor — appears under the name in italic Amiri.
        # "Son of the Land of Iran" — honoring his Iranian heritage.
        'title_fa':      'فرزند ایران زمین',
        'death_year':    2025,
        'death_date_fa': '۱۵ مه ۲۰۲۵',
        'dedication':    'یادبود',
        # "May his soul be joyful and his memory cherished" — classic Persian
        'epitaph':       'روحش شاد و یادش گرامی',
        # Khayyam quatrain on enjoying life while one lives — the user's brief
        'poem_lines': [
            'تا کی غم آن خورم که دارم یا نه',
            'وین عمر به خوشدلی گذارم یا نه',
            'پر کن قدح باده که معلومم نیست',
            'کاین دم که فرو برم برآرم یا نه',
        ],
        'poem_translation': (
            'تا کی غم خوریم از داشتن یا نداشتن؟ '
            'این عمر را به شادی بگذرانم یا نه؟ '
            'جام را پر کن — معلوم نیست این نفسی که فرو می‌برم، برآورم یا نه.'
        ),
        'poem_author': 'عمر خیام · رباعیات',
    },
}

today_md = now.strftime('%m-%d')
MEMORIAL = MEMORIAL_DATES.get(today_md)
MEMORIAL_MODE = MEMORIAL is not None
if MEMORIAL_MODE:
    years_passed = now.year - MEMORIAL['death_year']
    print(f"🕯️  Memorial mode: {MEMORIAL['name_fa']} — {years_passed} سال")


# --- 3d. RECIPE ROTATION (14-day cycle — kills the Mercimek-Çorbası-every-day rut) ---
# The model with no memory keeps defaulting to red-lentil soup. Pre-pick today's
# recipe in Python from a curated list, force the prompt to use it verbatim.
# Day-of-year modulo gives a stable 2-week rotation that's predictable.
RECIPE_ROTATION = [
    {'name_fa': 'قورمه‌سبزی', 'name_other': 'Ghormeh Sabzi · ایرانی کلاسیک',
     'hint': 'خورش سنتی ایرانی با سبزی معطر (تره، جعفری، شنبلیله)، لوبیا قرمز، گوشت گوسفند یا گوساله، لیمو عمانی.'},
    {'name_fa': 'ایمام بایلدی', 'name_other': 'İmam Bayıldı · ترکی کلاسیک',
     'hint': 'بادمجان شکم‌پر ترکی با گوجه، پیاز، سیر، روغن زیتون فراوان. به صورت سرد یا گرم سرو می‌شود.'},
    {'name_fa': 'ریزوتو زعفرانی', 'name_other': 'Risotto allo Zafferano · ایتالیایی میلانی',
     'hint': 'برنج آربوریو کرمی با کره، پیاز، شراب سفید، آب‌گوشت، پارمسان، و زعفران واقعی.'},
    {'name_fa': 'میرزا قاسمی', 'name_other': 'Mirza Ghassemi · گیلانی شمالی',
     'hint': 'بادمجان کبابی دودی با سیر فراوان، گوجه، تخم‌مرغ، زردچوبه. مزه دودی الکی نه — کاملاً روی شعله کبابی.'},
    {'name_fa': 'منمن', 'name_other': 'Menemen · صبحانه ترکی',
     'hint': 'تخم‌مرغ هم‌زده با گوجه‌فرنگی پخته، فلفل سبز، پیاز، روغن زیتون. به‌صورت سرپایی با نان تازه.'},
    {'name_fa': 'فسنجان با مرغ', 'name_other': 'Fesenjan · مجلسی ایرانی',
     'hint': 'خورش گردوی سابیده با رب انار غلیظ و مرغ. ترش‌و‌شیرین، تیره‌رنگ، با برنج زعفرانی.'},
    {'name_fa': 'سالاد شیرازی', 'name_other': 'Salad Shirazi · ساده ایرانی',
     'hint': 'خیار، گوجه، پیاز ریز نگینی، آبلیمو، نعناع تازه. خنک، تابستانی، در کنار هر غذا.'},
    {'name_fa': 'پاستا آلیو-اولیو', 'name_other': 'Pasta Aglio e Olio · ایتالیایی ناپلی',
     'hint': 'اسپاگتی با سیر، روغن زیتون، فلفل قرمز خرد، جعفری. ۱۵ دقیقه از شروع تا سرو.'},
    {'name_fa': 'کشک بادمجان', 'name_other': 'Kashk-e Bademjan · پیش‌غذای ایرانی',
     'hint': 'بادمجان سرخ‌شده با کشک، پیاز داغ، سیر داغ، نعناع داغ، گردو خرد. به‌صورت گرم با نان لواش.'},
    {'name_fa': 'زرشک‌پلو با مرغ', 'name_other': 'Zereshk Polo · مجلسی ایرانی',
     'hint': 'پلوی زرشک با کره و زعفران، همراه ران یا سینه مرغ پخته با پیاز و رب گوجه.'},
    {'name_fa': 'شکشوکا', 'name_other': 'Shakshuka · شامی شمال آفریقا',
     'hint': 'تخم‌مرغ نیم‌رو در سس گوجه‌فرنگی ادویه‌دار با فلفل دلمه، زیره، پاپریکا. در همان تابه سرو می‌شود.'},
    {'name_fa': 'مانتی', 'name_other': 'Mantı · دامپلینگ ترکی',
     'hint': 'دامپلینگ‌های ریز با گوشت چرخ‌کرده، آب‌پز، سرو با ماست سیردار و کره داغ با پاپریکا و نعناع.'},
    {'name_fa': 'استانبولی پلو', 'name_other': 'Estamboli Polo · خانگی ایرانی',
     'hint': 'پلوی گوجه با گوشت چرخ‌کرده، سیب‌زمینی، رب گوجه. کاملاً خانگی، یک‌قابلمه‌ای.'},
    {'name_fa': 'پاستا پستو', 'name_other': 'Pasta al Pesto · ایتالیایی لیگوریایی',
     'hint': 'پاستا با سس پستو خانگی (ریحان تازه، پارمسان، پکورینو، پاین‌نات، روغن زیتون، سیر).'},
]
todays_recipe = RECIPE_ROTATION[now.timetuple().tm_yday % len(RECIPE_ROTATION)]
print(f"🍽  Recipe today: {todays_recipe['name_fa']} ({todays_recipe['name_other']})")


# --- 3c. MEMORIAL CSS OVERRIDE & BANNER BUILDER ---
# When MEMORIAL_MODE is on, this CSS overrides the default palette to a muted
# mourning palette: aged parchment, charcoal ink, deep oxblood/maroon instead
# of vivid red, sage green, aged gold, dark navy. The body gradient also goes
# darker. Result: classy, quiet, sad — without being garish.
MEMORIAL_CSS_OVERRIDE = """<style>
:root{
  --paper:#ebe6da !important;
  --paper-dark:#cfc8b5 !important;
  --ink:#1c1c20 !important;
  --ink-soft:#34323a !important;
  --faded:#665f57 !important;
  --red:#5c3838 !important;        /* muted oxblood — used as primary accent */
  --red-dark:#3a2020 !important;
  --green:#3e4a3c !important;      /* deep sage */
  --gold:#7a6a4a !important;       /* aged brass */
  --blue:#2a3645 !important;       /* dark navy */
}
body{background:linear-gradient(#23201b,#13110d) !important;}
.section-header::before,.section-header::after{color:#8a6e4e !important;}
.memorial-banner{
  background:linear-gradient(135deg,#1e1e22,#36343a);
  color:#ebe6da;padding:22px 18px;margin-bottom:18px;
  text-align:center;border:1px solid #5c3838;border-radius:4px;
  box-shadow:0 4px 16px rgba(0,0,0,0.4);
}
.memorial-banner .candle{font-size:32px;display:block;margin-bottom:8px;line-height:1;}
.memorial-banner .dedication{
  font-size:11px;letter-spacing:3px;color:#c4b8a0;
  margin-bottom:6px;text-transform:uppercase;font-weight:600;
}
.memorial-banner .name{
  font-family:'Amiri','Vazirmatn',serif;font-size:26px;font-weight:700;
  margin:8px 0 2px;color:#f0ece0;letter-spacing:-0.5px;
}
.memorial-banner .name-en{
  font-family:'Amiri',serif;font-style:italic;font-size:13px;
  color:#a89c84;margin-bottom:8px;letter-spacing:1px;
}
.memorial-banner .title{
  font-family:'Amiri','Vazirmatn',serif;font-style:italic;
  font-size:15px;color:#d4c8b0;margin:4px 0 12px;
  letter-spacing:0.5px;
}
.memorial-banner .title::before,.memorial-banner .title::after{
  content:"✦";color:#8a6e4e;margin:0 8px;font-style:normal;font-size:10px;
}
.memorial-banner .dates{
  font-size:12px;color:#a89c84;margin-bottom:16px;
  font-family:'Amiri',serif;font-style:italic;
  padding-bottom:14px;border-bottom:1px solid rgba(196,184,160,0.25);
}
.memorial-banner .poem{
  font-family:'Amiri','Vazirmatn',serif;font-size:15px;line-height:2.1;
  font-style:italic;color:#f0ece0;margin:14px 8px 6px;
}
.memorial-banner .poem-translation{
  font-size:11.5px;line-height:1.7;color:#c4b8a0;
  margin:10px 16px 4px;text-align:justify;font-family:'Vazirmatn',sans-serif;
}
.memorial-banner .poem-author{
  font-size:10.5px;color:#a89c84;margin-top:10px;letter-spacing:1.5px;
}
.memorial-banner .epitaph{
  font-size:12px;color:#d4c8b0;margin-top:14px;padding-top:12px;
  border-top:1px solid rgba(196,184,160,0.25);
  font-family:'Amiri',serif;font-style:italic;
}
</style>"""


_FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def _fa_num(n):
    return str(n).translate(_FA_DIGITS)


def build_memorial_banner(m, years_passed):
    """Builds the memorial banner HTML for today's mourning edition."""
    poem_html = '<br>\n    '.join(m['poem_lines'])
    if years_passed <= 0:
        years_text = 'به یاد'
    elif years_passed == 1:
        years_text = 'نخستین سال از درگذشت'
    else:
        years_text = f"{_fa_num(years_passed)} سال از درگذشت"
    title_html = f'  <div class="title">{m["title_fa"]}</div>\n' if m.get('title_fa') else ''
    return f"""<div class="memorial-banner">
  <span class="candle">🕯</span>
  <div class="dedication">{m['dedication']}</div>
  <div class="name">{m['name_fa']}</div>
  <div class="name-en">— {m['name_en']} —</div>
{title_html}  <div class="dates">{m['death_date_fa']} · {years_text}</div>
  <div class="poem">
    {poem_html}
  </div>
  <div class="poem-translation">{m['poem_translation']}</div>
  <div class="poem-author">— {m['poem_author']} —</div>
  <div class="epitaph">{m['epitaph']}</div>
</div>
"""


MEMORIAL_BANNER = build_memorial_banner(MEMORIAL, now.year - MEMORIAL['death_year']) if MEMORIAL_MODE else ''


# --- 4. HTML SHELL (Python owns this — CSS never goes through the model) ---
_title_suffix = f" — نسخه یادبود {MEMORIAL['name_fa']}" if MEMORIAL_MODE else ""
_theme_color = "#5c3838" if MEMORIAL_MODE else "#d92020"

HTML_HEAD = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="{_theme_color}">
<title>روزنامه کوشاداسی هرالد سان — {edition_fa} {today_str}{_title_suffix}</title>
{HEAD_FONTS}
{CSS_TEMPLATE}
{MEMORIAL_CSS_OVERRIDE if MEMORIAL_MODE else ''}
</head>
<body>
<div class="paper">
{MEMORIAL_BANNER}"""

HTML_TAIL = """
</div>
</body>
</html>"""


# --- 4b. REAL NEWS FETCHERS (RSS + Telegram public channels) ---
# These give the model verified ground truth instead of forcing it to rely on
# Gemini's flaky search grounding for Iran news.

UA_HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; KusadasiHeraldBot/1.0)'}


def _clean(s):
    """Strip HTML tags + decode entities, normalize whitespace."""
    s = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', s, flags=re.DOTALL)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = htmllib.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()


def fetch_rss(url, source_name, max_items=6, encoding=None):
    """Pull headlines from an RSS feed. Returns list of {title, link, pub, summary}."""
    try:
        r = requests.get(url, headers=UA_HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"   RSS ✗ {source_name}: HTTP {r.status_code}")
            return []
        if encoding:
            r.encoding = encoding  # some Persian feeds need explicit utf-8
        items = re.findall(r'<item[^>]*>(.*?)</item>', r.text, re.DOTALL)[:max_items]
        out = []
        for item in items:
            def extract(pattern):
                m = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                return _clean(m.group(1)) if m else ''
            title = extract(r'<title[^>]*>(.*?)</title>')
            link = extract(r'<link[^>]*>(.*?)</link>')
            pub = extract(r'<pubDate[^>]*>(.*?)</pubDate>')
            desc = extract(r'<description[^>]*>(.*?)</description>')[:280]
            if title:
                out.append({'title': title, 'link': link, 'pub': pub, 'summary': desc})
        print(f"   RSS ✓ {source_name}: {len(out)} items")
        return out
    except Exception as e:
        print(f"   RSS ✗ {source_name}: {e}")
        return []


def fetch_telegram_public(username, max_msgs=6):
    """Scrape recent messages from a public Telegram channel via the t.me/s/ web preview.
    No auth required — works for any public channel."""
    url = f"https://t.me/s/{username}"
    try:
        r = requests.get(url, headers=UA_HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"   TG  ✗ @{username}: HTTP {r.status_code}")
            return []
        # Each message text block lives in a div with class tgme_widget_message_text
        msg_blocks = re.findall(
            r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
            r.text, re.DOTALL
        )
        # Dates are in <time datetime="..."> tags, one per message
        dates = re.findall(r'<time[^>]*datetime="([^"]+)"', r.text)
        out = []
        for i, block in enumerate(msg_blocks[-max_msgs:]):
            text = _clean(block)
            if not text:
                continue
            # Match date by position from the end
            idx_from_end = len(msg_blocks) - (len(msg_blocks) - max_msgs + i if len(msg_blocks) > max_msgs else i) - 1
            date = dates[-(idx_from_end + 1)] if idx_from_end < len(dates) else ''
            out.append({'text': text[:280], 'date': date})
        out.reverse()  # newest first
        print(f"   TG  ✓ @{username}: {len(out)} messages")
        return out
    except Exception as e:
        print(f"   TG  ✗ @{username}: {e}")
        return []


def fetch_khabarvarzeshi(max_items=6):
    """Pull khabarvarzeshi.com RSS — replaces Varzesh3 which has been frozen
    at 2025-08-25 since at least May 2026. This feed is live and updates
    several times per day with Persian sports news (Iranian + global)."""
    try:
        r = requests.get('https://khabarvarzeshi.com/rss', headers=UA_HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"   KV  ✗ khabarvarzeshi: HTTP {r.status_code}")
            return []
        r.encoding = 'utf-8'
        items = re.findall(r'<item[^>]*>(.*?)</item>', r.text, re.DOTALL)[:max_items]
        out = []
        for item in items:
            def extract(pattern):
                m = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                return _clean(m.group(1)) if m else ''
            title = extract(r'<title[^>]*>(.*?)</title>')
            if not title:
                continue
            out.append({
                'title': title,
                'link': extract(r'<link[^>]*>(.*?)</link>'),
                'pub': extract(r'<pubDate[^>]*>(.*?)</pubDate>'),
                'summary': extract(r'<description[^>]*>(.*?)</description>')[:280],
            })
        print(f"   KV  ✓ khabarvarzeshi: {len(out)} items")
        return out
    except Exception as e:
        print(f"   KV  ✗ khabarvarzeshi: {e}")
        return []


def fetch_iranwire(max_items=8, sports_only=False):
    """Pull IranWire RSS. Two unusual quirks of this feed:
    1. Items are ordered OLDEST-FIRST (most feeds go newest-first), so we
       reverse before slicing.
    2. It returns ~700 items, so reversing+slicing is critical for freshness."""
    try:
        r = requests.get('https://iranwire.com/fa/feed', headers=UA_HEADERS, timeout=25)
        if r.status_code != 200:
            print(f"   IW  ✗ IranWire: HTTP {r.status_code}")
            return []
        r.encoding = 'utf-8'
        items = re.findall(r'<item[^>]*>(.*?)</item>', r.text, re.DOTALL)
        items.reverse()  # IranWire ships oldest→newest; flip it

        # Sports filter: positive keywords + maritime-context exclusion list to
        # avoid matching "کشتی" when it means "ship" (Hormuz traffic news).
        SPORTS_POS = [
            'استقلال ', 'پرسپولیس', 'سپاهان', 'تراکتور', 'فوتبال',
            'تیم ملی', 'فدراسیون فوتبال', 'فیفا', 'یوفا', 'جام جهانی',
            'لیگ برتر', 'لالیگا', 'سوپرلیگ', 'پریمیرلیگ', 'سری آ',
            'بازیکن', 'گلزن', 'مربی', 'کاپیتان', 'ورزشگاه', 'استادیوم',
            'کشتی فرنگی', 'کشتی آزاد', 'والیبال', 'بسکتبال', 'وزنه‌برداری',
            'تکواندو', 'کاراته', 'دو میدانی', 'شنا قهرمانی',
            'طارمی', 'آزمون', 'جهانبخش', 'دایی', 'علی پروین',
            'نقل و انتقالات', 'مسابقه قهرمانی', 'بازی دوستانه',
        ]
        SPORTS_NEG = [  # maritime / military false positives for "کشتی"
            'تنگه هرمز', 'سپاه پاسداران', 'بندرعباس', 'توقیف کشتی',
            'کشتی تجاری', 'کشتی نفتکش', 'کشتی توقیف', 'حمله به کشتی',
        ]

        out = []
        for item in items:
            def extract(pattern):
                m = re.search(pattern, item, re.DOTALL | re.IGNORECASE)
                return _clean(m.group(1)) if m else ''
            title = extract(r'<title[^>]*>(.*?)</title>')
            if not title:
                continue
            if sports_only:
                if not any(kw in title for kw in SPORTS_POS):
                    continue
                if any(kw in title for kw in SPORTS_NEG):
                    continue
            out.append({
                'title': title,
                'link': extract(r'<link[^>]*>(.*?)</link>'),
                'pub': extract(r'<pubDate[^>]*>(.*?)</pubDate>'),
                'summary': extract(r'<description[^>]*>(.*?)</description>')[:280],
            })
            if len(out) >= max_items:
                break
        label = "sports" if sports_only else "general"
        print(f"   IW  ✓ IranWire ({label}): {len(out)} items")
        return out
    except Exception as e:
        print(f"   IW  ✗ IranWire: {e}")
        return []


def build_news_context():
    """Fetch real news headlines from RSS + Telegram. Returns a Persian-language
    block to inject into the prompt."""
    print("📰 Fetching real news feeds...")
    parts = []

    # RSS feeds — websites that publish proper feeds
    rss_sources = [
        ('BBC Persian',       'https://feeds.bbci.co.uk/persian/rss.xml'),
        ('Euronews Persian',  'https://parsi.euronews.com/rss'),
    ]
    for name, url in rss_sources:
        items = fetch_rss(url, name, max_items=5)
        if items:
            parts.append(f"\n──── منبع: {name} (RSS امروز) ────")
            for it in items:
                line = f"• «{it['title']}»"
                if it['pub']:
                    line += f"  [{it['pub']}]"
                if it['link']:
                    line += f"\n  🔗 {it['link']}"
                if it['summary']:
                    line += f"\n  📝 {it['summary']}"
                parts.append(line)

    # IranWire — general news, newest first
    iw_general = fetch_iranwire(max_items=6, sports_only=False)
    if iw_general:
        parts.append("\n──── منبع: IranWire (تازه‌ترین — عمومی) ────")
        for it in iw_general:
            line = f"• «{it['title']}»"
            if it['pub']:
                line += f"  [{it['pub']}]"
            if it['link']:
                line += f"\n  🔗 {it['link']}"
            if it['summary']:
                line += f"\n  📝 {it['summary']}"
            parts.append(line)

    # IranWire — sports filter (replaces dead Varzesh3 partially)
    iw_sports = fetch_iranwire(max_items=4, sports_only=True)
    if iw_sports:
        parts.append("\n──── منبع: IranWire (ورزش) ────")
        for it in iw_sports:
            line = f"• «{it['title']}»"
            if it['pub']:
                line += f"  [{it['pub']}]"
            if it['link']:
                line += f"\n  🔗 {it['link']}"
            if it['summary']:
                line += f"\n  📝 {it['summary']}"
            parts.append(line)

    # khabarvarzeshi — live Persian sports feed (Varzesh3 is dead, frozen 2025-08-25)
    kv_items = fetch_khabarvarzeshi(max_items=6)
    if kv_items:
        parts.append("\n──── منبع: khabarvarzeshi (ورزش امروز · ایران و جهان) ────")
        for it in kv_items:
            line = f"• «{it['title']}»"
            if it['pub']:
                line += f"  [{it['pub']}]"
            if it['link']:
                line += f"\n  🔗 {it['link']}"
            if it['summary']:
                line += f"\n  📝 {it['summary']}"
            parts.append(line)

    # Telegram public channels — for outlets without good RSS, or to capture
    # different ideological angles. User-specified: bbcpersian (Western/foreign),
    # mypersia24 (Iran-government-leaning), euronewspe (European moderate).
    tg_channels = [
        ('bbcpersian',  'BBC Persian (Telegram)'),
        ('euronewspe',  'Euronews Persian (Telegram)'),
        ('mypersia24',  'MyPersia24 — Iran-leaning (Telegram)'),
    ]
    for handle, label in tg_channels:
        msgs = fetch_telegram_public(handle, max_msgs=5)
        if msgs:
            parts.append(f"\n──── منبع: {label} — @{handle} ────")
            for m in msgs:
                line = f"• {m['text']}"
                if m['date']:
                    line += f"  [{m['date']}]"
                line += f"\n  🔗 https://t.me/{handle}"
                parts.append(line)

    if not parts:
        return "(فید زنده امروز قابل دسترسی نیست — از Google Search استفاده کنید و قوانین ضد-ساختن خبر را رعایت کنید.)"

    headline_count = sum(1 for p in parts if p.startswith('•'))
    source_count = sum(1 for p in parts if 'منبع:' in p)
    print(f"📰 News context built: {headline_count} headlines across {source_count} sources")
    return '\n'.join(parts)


NEWS_CONTEXT = build_news_context()


# --- 5. PROMPT (asks for inner content only — saves ~5K tokens of CSS regurgitation) ---
_memorial_note = ""
if MEMORIAL_MODE:
    _memorial_note = f"""
══════════════════════════════════════════════════════════════
== 🕯 نسخه یادبود — توجه ویژه ==
══════════════════════════════════════════════════════════════

امروز ({today_str}) سالگرد درگذشت **{MEMORIAL['name_fa']}** ({MEMORIAL['name_en']}) است.
بالای ماست‌هد یک بنر یادبود توسط Python اضافه شده — لازم نیست شما آن را تولید کنید.

نکات نسخه یادبود:
• بنر یادبود را تولید **نکنید** — Python خودش آن را اضافه می‌کند.
• محتوای روزنامه را به طور معمول بنویسید (همان بخش‌های همیشگی).
• فقط در «پیام پایانی» (closing-text) لحن گرم‌تر، کمی فلسفی، و یادآور ارزش لحظه باشد. به طور صریح به مرحوم اشاره نکنید — اما حالی شاعرانه و آرام داشته باشید.
• اگر در «در چنین روزی» یک رویداد تاریخی فلسفی یا یادآور زندگی هست، آن را اولویت دهید.

══════════════════════════════════════════════════════════════
"""

PROMPT = f"""شما سردبیر ارشد روزنامه «کوشاداسی هرالد سان» — روزنامه فارسی‌زبان روزانه برای جامعه فارسی‌زبان در کوشاداسی (سواحل اژه ترکیه) و خارج.

تاریخ امروز میلادی: {today_human_en} ({today_str})
نوبت انتشار: {edition_fa} ({edition_en})
{_memorial_note}

══════════════════════════════════════════════════════════════
== ⛔ ممنوعیت نشانگرهای داخلی در خروجی ⛔ ==
══════════════════════════════════════════════════════════════

**هرگز** این نشانگرها را در متن خروجی ننویسید — این‌ها فقط برای استدلال داخلی شما هستند، نه برای خواننده:

❌ `[cite: 19 (from prompt)]`
❌ `[cite: 8 (from previous search)]`
❌ `(from prompt)` در هیچ شکلی
❌ `(from previous search)` در هیچ شکلی
❌ `[cite: ...]` هر شکل بازوی دیگری

خواننده نباید هیچ بریده‌ای از کد یا نشانگرهای کاری شما را ببیند. اگر می‌خواهید منبع را نشان دهید، فقط در byline-row با فرمت طبیعی: «به نقل از BBC Persian، ۱۱ مه ۲۰۲۶».

══════════════════════════════════════════════════════════════
== ⚠️ قانون مطلق: ممنوعیت ساختن خبر ⚠️ ==
══════════════════════════════════════════════════════════════

این مهم‌ترین قانون است — تخلف از آن اعتبار روزنامه را نابود می‌کند:

❌ **هرگز خبر نسازید.** اگر Google Search نتیجه قابل تأیید نداد، خبر را ننویسید.
❌ **هرگز نقل قول نسازید** — هر blockquote باید عیناً از یک منبع واقعی برگرفته شود، با ذکر URL یا نام مقاله.
❌ **هرگز امتیاز یا نتیجه بازی نسازید** — اگر نمی‌توانید نتیجه را در یک منبع ورزشی تأیید کنید، نتیجه ننویسید.
❌ **هرگز سخن از زبان افراد متوفی نقل نکنید.** افرادی که در ۲۰۲۶ زنده نیستند را نقل قول نکنید.

**حقایق ثابت برای ۱۱ مه ۲۰۲۶ (به‌خاطر بسپارید):**
• حسین امیرعبداللهیان (وزیر سابق خارجه ایران): **در ۱۹ مه ۲۰۲۴ در سقوط بالگرد درگذشت**. زنده نیست. نقل قول نکنید.
• ابراهیم رئیسی (رئیس‌جمهور سابق ایران): **در همان حادثه ۱۹ مه ۲۰۲۴ درگذشت**. زنده نیست.
• وزیر فعلی خارجه ایران: عباس عراقچی است (مگر این که جستجو تغییر را تأیید کند).
• ایران در سال ۲۰۲۶ در شرایط جنگی/درگیری است. **لیگ برتر فوتبال ایران ممکن است معلق باشد.** قبل از نوشتن از بازی، وضعیت لیگ را در جستجو تأیید کنید. نتایج تخیلی ساختن ممنوع است.
• ترامپ رئیس‌جمهور آمریکا است.
• ملونی نخست‌وزیر ایتالیا است (مگر تغییر را در جستجو ببینید).

══════════════════════════════════════════════════════════════
== ⭐ اخبار واقعی و تأیید شده امروز از فیدهای زنده ⭐ ==
══════════════════════════════════════════════════════════════

این تیترها و متن‌ها همین لحظه از RSS و کانال‌های تلگرام BBC Persian, Euronews فارسی, Radio Farda, VOA Persian, MyPersia24 پایین آمده‌اند. **این محتوا واقعی، تأیید شده، و امروزی است.**

برای بخش «گزارش جهانی · ایران» (بخش ۳):
✓ **حتماً** ۲ تا ۳ تیتر از این فهرست انتخاب کنید — ترجیحاً از منابع متنوع برای تعادل دیدگاه (یک از BBC/Euronews غربی، یک از MyPersia24 داخلی-گرا اگر موجود است).
✓ هر مقاله را با گسترش معنای تیتر و خلاصه بسازید — بدون اضافه کردن نقل قول جدید.
✓ در byline-row حتماً منبع واقعی و URL واقعی را بنویسید (همان که در فهرست زیر آمده).
✓ blockquote فقط در صورتی استفاده کنید که نقل قول مستقیم در خلاصه RSS موجود باشد.

برای بخش‌های دیگر (سوکه، کوشاداسی، رم، بارسلونا، ورزش‌ها) اگر تیتر مرتبط در این فهرست هست از آن استفاده کنید، در غیر این صورت از Google Search کمک بگیرید — اما **قوانین ضد-ساختن خبر را رعایت کنید**.

{NEWS_CONTEXT}

══════════════════════════════════════════════════════════════
== الزام منبع: هر مقاله باید منبع واقعی داشته باشد ==
══════════════════════════════════════════════════════════════

**byline-row هر مقاله باید نام دقیق منبع + تاریخ نشر را داشته باشد** که در نتایج Google Search یافتید:

✓ صحیح: `<span class="name">به نقل از BBC Persian، ۹ مه ۲۰۲۶</span>`
✓ صحیح: `<span class="name">Hürriyet Aydın، ۱۰ مه ۲۰۲۶</span>`
✗ غلط: `<span class="name">تحریریه</span>` یا `<span class="name">گروه ورزشی</span>` بدون منبع واقعی

اگر یک مقاله نمی‌تواند یک منبع واقعی و تاریخ مشخص داشته باشد، آن مقاله را ننویسید — placeholder بگذارید:

«امروز خبر تأیید شده‌ای از این بخش در منابع واقعی موجود نیست.»

placeholder **بهتر از ساختن خبر است.** هرگز با ساختن خبر فضا را پر نکنید.

══════════════════════════════════════════════════════════════
== مهم‌ترین قانون: تازگی و دقت ==
══════════════════════════════════════════════════════════════

از Google Search **حتماً** برای پیدا کردن اخبار واقعی استفاده کنید. **چندین جستجو** انجام دهید — اگر اولین جستجو نتیجه نداد، با کلمات کلیدی متفاوت دوباره جستجو کنید.

**هر مقاله باید حداقل یکی از این موارد را داشته باشد:**
✓ نام مشخص یک شخص (سیاستمدار، ورزشکار، هنرمند، مقام رسمی)
✓ تاریخ مشخص در ۳۰ روز گذشته
✓ عدد، آمار، یا امتیاز دقیق
✓ نام مکان دقیق (موزه، رستوران، استادیوم، خیابان — نه فقط نام شهر)
✓ نقل‌قول مستقیم با ذکر گوینده

**انواع قابل قبول محتوا (بسیار وسیع‌تر از فقط نتیجه بازی یا حادثه روز):**
✓ تحلیل با ارجاع به یک رخداد مشخص ماه گذشته
✓ گزارش از یک رویداد در حال جریان (نمایشگاه، فستیوال) با تاریخ شروع/پایان
✓ پیش‌نمایش بازی، رویداد، یا کنفرانس آینده با تاریخ مشخص
✓ آمار اقتصادی/گردشگری منطقه با اعداد دقیق
✓ نقل قول از مقام محلی در یک مصاحبه یا اعلامیه ماه گذشته
✓ توسعه پروژه‌ای محلی با نام پیمانکار/مقام مسئول

**فقط در صورتی که پس از ۳ بار جستجوی متفاوت** هیچ محتوایی با حداقل یک عنصر مشخص پیدا نکردید، به جای آن بنویسید:
«امروز خبر برجسته‌ای از این بخش در منابع تأیید شده موجود نیست.»

این placeholder باید واقعاً آخرین چاره باشد — نه گزینه پیش‌فرض. بیشتر بخش‌ها باید محتوای واقعی داشته باشند.

══════════════════════════════════════════════════════════════
== عبارات و سبک‌های اکیداً ممنوع ==
══════════════════════════════════════════════════════════════

این عبارات نشانه نوشتن کلی و بی‌فایده هستند — هرگز استفاده نکنید:

✗ «رقابت تنگاتنگ در هفته‌های پایانی»
✗ «فصل پررونق گردشگری تابستانی» / «آماده استقبال از فصل»
✗ «امیدها برای ...»
✗ «در هفته‌های اخیر» / «در ماه‌های اخیر»
✗ «تحلیلگران معتقدند» (بدون نام تحلیلگر)
✗ «به گزارش رسانه‌ها» / «منابع آگاه می‌گویند»
✗ «هواداران با شور و هیجان» / «هیجان در اوج است»
✗ «تأثیر مثبتی بر اقتصاد محلی خواهد داشت»

**معیار:** اگر متنی را می‌توان امروز، فردا، یا ماهی بعد هم نوشت — آن متن غلط است. حذف کنید.

══════════════════════════════════════════════════════════════
== منابع تأیید شده ==
══════════════════════════════════════════════════════════════

- بی‌بی‌سی فارسی، صدای آمریکا فارسی، ایران اینترنشنال، یورونیوز فارسی
- رسانه‌های معتبر داخل ایران (در صورت دقیق بودن)
- ترکیه: Hürriyet, Habertürk, Anadolu Agency, Aydın Post, Söke Haberleri
- ایتالیا: ANSA, La Repubblica, Corriere della Sera
- اسپانیا: El País, La Vanguardia, ABC Cultural
- ورزش ایران: طرفداری، وارزش، فدراسیون فوتبال
- Turkish Süper Lig: TFF, Fanatik

══════════════════════════════════════════════════════════════
== خروجی ==
══════════════════════════════════════════════════════════════

فقط HTML داخلی div.paper را تولید کنید. هیچ <!DOCTYPE>, <html>, <head>, <body>, <style>, <link>, <div class="paper">, یا </div> پایانی ننویسید — Python آن‌ها را اضافه می‌کند.
شروع: <div class="masthead">. پایان: </div> آخر footer.
بدون ```html و بدون توضیح اضافی.

== ماست‌هد دقیقاً ==
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

== کلاس‌های CSS مجاز ==
.teaser-bar | .article | .article-kicker | h2.lead | h2.sub-lead | h3.deck | .byline-row > .headshot, .name | .drop | blockquote
.section-header (با .red .blue .green .gold)
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

══════════════════════════════════════════════════════════════
== بخش‌ها به ترتیب ==
══════════════════════════════════════════════════════════════

**۱.** ماست‌هد (همان‌طور که بالا آمد).

**۲.** <div class="teaser-bar"><strong>◂ در این شماره ◂</strong> ۴ تا ۶ تیتر امروز · جدا شده · با · نقطه‌های پررنگ</div>

**۳.** section-header red «گزارش جهانی · ایران»
   ۲ تا ۳ <article class="article">. هر مقاله: kicker, h2.lead, h3.deck, byline-row, پاراگراف‌ها (اولی با drop). حداقل یک blockquote با نام منبع. **نام شخص یا تاریخ مشخص الزامی.**

**۴.** section-header gold «ورزش ایران و جهان»
   ۱ تا ۲ مقاله. **منبع اصلی: تیترهای khabarvarzeshi و IranWire (ورزش) از فهرست بالا.**

   ⛔ **اکیداً ممنوع: استفاده از خبرگزاری Varzesh3.** فید Varzesh3 از مرداد ۱۴۰۴ به‌روزرسانی نشده و اخبار آن کاملاً قدیمی است. هرگز به Varzesh3 ارجاع ندهید.

   محتوای قابل قبول (بر اساس تیترهای **امروز** از khabarvarzeshi و IranWire):
   • نتیجه بازی، نقل و انتقالات، یا اعلامیه باشگاه/فدراسیون با تاریخ مشخص
   • وضعیت ستاره‌های ایرانی در لیگ‌های خارجی (طارمی، جهانبخش، آزمون)
   • اخبار جام جهانی ۲۰۲۶ یا تیم ملی
   • اخبار لیگ برتر ایران، استقلال، پرسپولیس، سپاهان، تراکتور
   • کشتی، والیبال، بسکتبال، تکواندو — رویدادهای امروز
   **byline حتماً نام منبع واقعی (khabarvarzeshi.com یا IranWire) + URL واقعی از فهرست بالا.**
   تاریخ بازی یا رویداد باید در ۷ روز اخیر باشد. اخبار قدیمی‌تر از یک هفته ننویسید.

**۵.** section-header «اخبار محلی · کوشاداسی، سوکه، آیدین»
   **دقیقاً ۳ مقاله. محتوای قابل قبول بسیار وسیع است:**

   • مقاله ۵.۱ — خبری از **سوکه** یا منطقه نزدیک سوکه:
     - اعلامیه شهرداری Söke یا کایماکام
     - رویداد بازار، فستیوال، یا کشاورزی فصلی (پنبه، انجیر، زیتون)
     - گزارش از کارگاه‌های صنایع دستی محلی
     - تحول راه/زیرساخت با نام پیمانکار
     - اخبار آبیاری، آب، یا محیط زیست رودخانه Büyük Menderes
     جستجو: «Söke belediyesi» OR «Söke haberleri» OR «Aydın Söke».

   • مقاله ۵.۲ — خبر **عمومی کوشاداسی** (غیر فرهنگی):
     - بندر کوشاداسی: شماره و نوع کشتی‌های کروز پهلوگرفته با نام و تاریخ
     - اعلامیه شهرداری کوشاداسی یا فرماندار آیدین
     - حادثه، گزارش پلیس، اطلاعیه ترافیک
     - آمار گردشگری ماه گذشته با عدد دقیق
     - اخبار توسعه (هتل جدید، مرکز خرید، پروژه)
     جستجو: «Kuşadası belediyesi» OR «Kuşadası limanı» OR «Aydın Post Kuşadası».

   • مقاله ۵.۳ — خبر **فرهنگی کوشاداسی یا منطقه افسوس**:
     - رویداد در آمفی‌تئاتر افسوس (تور، نمایش، کنسرت) با تاریخ مشخص
     - حفاری یا کشف باستان‌شناسی در افسوس یا منطقه
     - کنسرت یا نمایشگاه در کوشاداسی یا نزدیک
     - رستوران یا کافه جدید با نام و موقعیت
     - فستیوال محلی (رویداد ماهانه/فصلی) با تاریخ
     جستجو: «Efes Antik Kenti» OR «Kuşadası kültür sanat» OR «Aydın etkinlik».

**۶.** section-header gold «ورزش محلی · ترکیه»
   ۱ مقاله. محتوای قابل قبول:
   • نتیجه بازی Süper Lig (Galatasaray, Fenerbahçe, Beşiktaş, Trabzonspor, ...) با امتیاز و گلزن
   • وضعیت جدول لیگ یا تیم در رقابت‌های اروپایی (UEFA)
   • پیش‌نمایش بازی آخر هفته با تاریخ و سعت
   • نقل و انتقالات با نام بازیکن
   جستجو: «Süper Lig» OR «Galatasaray Fenerbahçe» OR «Türkiye Kupası».

**۷.** section-header blue «گزارش از رم»
   **دقیقاً ۲ مقاله. فوتبال اکیداً ممنوع.**

   • مقاله ۷.۱ — **فرهنگی**:
     - نمایشگاه در حال جریان در یک موزه/گالری مشخص (Galleria Borghese, MAXXI, Palazzo delle Esposizioni, Vatican Museums) با تاریخ شروع/پایان
     - اپرا یا کنسرت در Teatro dell'Opera, Auditorium Parco della Musica
     - فستیوال یا رویداد فرهنگی (Festa della Repubblica, RomaEuropa Festival)
     - حفاری یا کشف باستان‌شناسی جدید با نام محقق
     - اکران فیلم ایتالیایی با نام کارگردان و سینما
     جستجو: «mostra Roma» OR «Galleria Borghese exhibition» OR «Roma cultura».

   • مقاله ۷.۲ — **سیاسی**:
     - اعلامیه دولت ملونی با تاریخ و موضوع مشخص
     - رای پارلمان یا قانون جدید
     - دیدار دیپلماتیک با نام مقامات
     - رابطه با اتحادیه اروپا، ایالات متحده، یا کشور مشخص
     - اعتراض، اعتصاب، یا رویداد سیاسی شهر رم
     جستجو: «Meloni governo» OR «politica italiana» OR «Roma Camera deputati».

**۸.** section-header green «بارسلونا · فرهنگ»
   **دقیقاً ۱ مقاله — فقط فرهنگی. FC Barcelona و فوتبال اکیداً ممنوع.**
   محتوای قابل قبول:
   • نمایشگاه در Museu Picasso, MACBA, MNAC, CCCB, CaixaForum (با تاریخ شروع/پایان)
   • کنسرت در Palau de la Música Catalana یا L'Auditori
   • نمایش در Liceu (اپرا)
   • معماری گاودی: تور، رویداد، رستوراسیون با تاریخ
   • فستیوال (Sónar, Primavera Sound, Mercé) با تاریخ مشخص
   • رستوران یا فعالیت گستروانتومی با نام سرآشپز
   • مد، طراحی، یا هنر معاصر کاتالان
   جستجو: «Barcelona cultura agenda» OR «Museu Picasso exhibition» OR «Palau Música concert» OR «Sagrada Família».

**۹.** section-header blue «آب و هوا»
   div.box: weather-grid (۳ روز کوشاداسی) + city-weather (کوشاداسی، رم، بارسلونا). دما و وضعیت دقیق.

**۱۰.** div.turkish-word — **ترانه ترکی روز** (Turkish Song of the Day):

   ⚠️ **قانون مهم برای لینک Spotify و YouTube:**
   - **هرگز** از فرمت `https://open.spotify.com/track/<id>` استفاده نکنید — شما نمی‌توانید شناسه‌های واقعی track را بدانید و حدس زدن آن‌ها به لینک مرده منجر می‌شود.
   - **همیشه** از URL جستجو استفاده کنید که در همه جا (از جمله ترکیه) کار می‌کند:
     - Spotify: `https://open.spotify.com/search/[ARTIST]%20[TITLE]` (space → %20)
     - YouTube: `https://www.youtube.com/results?search_query=[ARTIST]+[TITLE]` (space → +)

   ساختار دقیق:
   ```
   <div class="turkish-word">
     <div class="turkish-title">★ ترانه ترکی روز ★</div>
     <div class="turkish-main">[نام ترانه]</div>
     <div class="turkish-meaning">[نام خواننده] · [سال انتشار]</div>
     <div class="turkish-ex">
       <strong>[یک مصرع ترکی]</strong><br>
       [ترجمه فارسی همان مصرع]<br>
       <a href="https://open.spotify.com/search/[ARTIST]%20[TITLE]" target="_blank">🎧 Spotify</a> ·
       <a href="https://www.youtube.com/results?search_query=[ARTIST]+[TITLE]" target="_blank">▶ YouTube</a>
     </div>
   </div>
   ```

   مثال کامل و درست برای ترانه «Dudu» اثر Tarkan:
   ```
   <a href="https://open.spotify.com/search/Tarkan%20Dudu" target="_blank">🎧 Spotify</a> ·
   <a href="https://www.youtube.com/results?search_query=Tarkan+Dudu" target="_blank">▶ YouTube</a>
   ```

   - یک ترانه ترکی معروف و کلاسیک یا محبوب امروزی (Tarkan, Sezen Aksu, Barış Manço, Müslüm Gürses, Ajda Pekkan, Aleyna Tilki, Mabel Matiz, Tarkan Tevetoğlu, Emre Aydın, Sıla, Ezhel و...).
   - ۱ تا ۲ مصرع کوتاه از متن ترانه به ترکی و ترجمه فارسی.
   - **در URLها از فاصله یا کاراکترهای فارسی استفاده نکنید** — فقط نام انگلیسی/ترکی هنرمند و آهنگ. فاصله = `%20` در Spotify، `+` در YouTube.

**۱۱.** div.history-box — ۳ رویداد تاریخی این روز (با history-year پررنگ).

**۱۲.** div.health-tip — مناسب سن ۷۰+، مرتبط با هوای امروز یا فصل.

**۱۳.** section-header green «آشپزی · دستور روز»
   **دستور امروز:** {todays_recipe['name_fa']} ({todays_recipe['name_other']})
   **راهنما / شرح کلی:** {todays_recipe['hint']}

   شما **حتماً** همین دستور را بنویسید — تنوع روزانه یک ارزش جدی این روزنامه است.
   • recipe-title: نام فارسی دستور
   • recipe-heading «📌 اجزا»: فهرست دقیق مواد لازم برای ۴ نفر
   • recipe-heading «🧑‍🍳 طرز تهیه»: مراحل شماره‌گذاری شده (۶ تا ۸ مرحله)
   • recipe-heading «💚 یادداشت سلامتی»: یک پاراگراف کوتاه درباره ارزش غذایی برای سن ۷۰+

   ⛔ **اکیداً ممنوع:** سوپ عدس قرمز (Mercimek Çorbası / مرسیمک چوربا‌سی) — این دستور به حد کافی پخته شده و خوانندگان از تکرار آن خسته شده‌اند. هرگز نوشته نشود.

**۱۴.** div.migros-box — مواد لازم **همان دستور بالا ({todays_recipe['name_fa']})** با قیمت‌های روز.
   **دقت قیمت:** قیمت‌های واقعی فعلی در سوپرمارکت میگروس ترکیه (مه ۲۰۲۶). اگر قیمت دقیق در دسترس نیست، در پایان جعبه (داخل migros-total یا قبل از آن) عبارت «قیمت‌ها تقریبی — لطفاً در فروشگاه تأیید کنید» را اضافه کنید.

**۱۵.** div.closing — پیام پایانی گرم.

**۱۶.** div.footer — colophon، فهرست منابع امروز (نام دقیق رسانه‌هایی که واقعاً استفاده شده‌اند، نه فهرست عمومی)، تاریخ شماره بعدی. **بدون ایمیل، بدون آدرس وب، بدون «info@» یا «https».**

══════════════════════════════════════════════════════════════
**یادآوری نهایی:** قبل از نوشتن، خود را بپرسید: «این جمله را آیا فقط امروز می‌توانم بنویسم — با نام، تاریخ، یا عدد مشخص؟» اگر نه، بازنویسی کنید.

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
    # Try in this order. Less popular models last — they're rarely overloaded.
    # Each step gets its own retry loop with exponential backoff.
    attempts = [
        (MODEL, True),                  # preferred model with grounding (best content)
        (MODEL, False),                 # preferred model alone
        ("gemini-2.5-flash-lite", False),   # cheaper sibling, much less crowded
        ("gemini-2.0-flash", False),    # older generation, even less crowded
        ("gemini-2.5-pro", False),      # last resort — usually quota-limited on free tier
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
    # Strip Gemini citation leaks that pollute the final HTML:
    # e.g. "[cite: 19 (from prompt), 4 (from prompt)]" or "[cite: 8 (from previous search)]"
    # The model emits these as internal reasoning markers; they must never reach the reader.
    s = re.sub(r'\s*\[cite[^\]]*\]', '', s)
    # Also strip any stray "(from prompt)" / "(from previous search)" parentheticals
    # that might escape outside of brackets
    s = re.sub(r'\s*\((?:from prompt|from previous search)[^)]*\)', '', s)
    # Strip stray "(cite N)" style if any
    s = re.sub(r'\s*\(cite\s+\d+[^)]*\)', '', s)
    # Fix fabricated Spotify track URLs. Gemini can't actually know real track IDs,
    # so any `/track/<garbled>` link is a hallucination → dead link in Turkey.
    # Convert to a Spotify search URL using nearby text from the same .turkish-word block.
    def _fix_spotify(match):
        block = match.group(0)
        # Pull artist (turkish-meaning) and title (turkish-main) out of the block
        title_m = re.search(r'<div class="turkish-main"[^>]*>([^<]+)</div>', block)
        artist_m = re.search(r'<div class="turkish-meaning"[^>]*>([^·<]+)', block)
        title = (title_m.group(1) if title_m else '').strip()
        artist = (artist_m.group(1) if artist_m else '').strip()
        if not title:
            return block  # can't fix without title — leave it
        query = f"{artist} {title}".strip()
        spotify_q = query.replace(' ', '%20')
        youtube_q = query.replace(' ', '+')
        # Replace any spotify track URL with the search URL
        block = re.sub(
            r'https?://open\.spotify\.com/track/[A-Za-z0-9_-]+',
            f'https://open.spotify.com/search/{spotify_q}',
            block
        )
        # Also fix any youtube watch URL with a search URL
        block = re.sub(
            r'https?://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]+',
            f'https://www.youtube.com/results?search_query={youtube_q}',
            block
        )
        return block
    s = re.sub(
        r'<div class="turkish-word"[^>]*>.*?</div>\s*</div>',
        _fix_spotify,
        s,
        flags=re.DOTALL
    )
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
