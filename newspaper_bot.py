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
.poetry-box{background:linear-gradient(135deg,#f4ecdf,#eadfc6);border-right:4px solid var(--gold);padding:14px 16px;margin:14px 0;text-align:center;}
.poetry-title{font-size:11px;color:var(--gold);font-weight:700;letter-spacing:1.5px;margin-bottom:6px;}
.poetry-verses{font-family:'Amiri',serif;font-size:15px;line-height:2;color:var(--ink);margin:8px 0;direction:rtl;}
.poetry-translation{font-size:12px;color:var(--ink-soft);font-style:italic;margin-top:6px;line-height:1.7;}
.poetry-attribution{font-size:11px;color:var(--faded);margin-top:8px;font-weight:600;letter-spacing:0.5px;}
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
# Split at noon local: anything AM local = morning edition, PM = evening.
# Wider than the previous 7-14 window, which missed 05:00-06:00 local (what
# the current cron fires at when GHA delivers on time) — that bug had both
# daily runs registering as Evening for over a week.
is_morning = local_hour < 12
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


# --- 3e. TURKISH SONG ROTATION (14-day cycle — kills the "Tarkan Dudu every day" rut) ---
SONG_ROTATION = [
    {'artist': 'Tarkan',          'title': 'Dudu',                    'year': 2003,
     'line_tr': 'Ağlamadan ayrılık olmaz, hatıralar uslu durmaz',
     'line_fa': 'جدایی بدون گریه نمی‌شود، خاطرات آرام نمی‌گیرند'},
    {'artist': 'Sezen Aksu',      'title': 'Geri Dön',                'year': 1988,
     'line_tr': 'Geri dön, kal yanımda ne olur',
     'line_fa': 'برگرد، کنارم بمان، خواهش می‌کنم'},
    {'artist': 'Barış Manço',     'title': 'Gülpembe',                'year': 1981,
     'line_tr': 'Bizim gülpembe annem, bizim gülpembe',
     'line_fa': 'مادر گل‌پنبه‌ای ما، گل‌پنبه‌ای ما'},
    {'artist': 'Müslüm Gürses',   'title': 'Affet',                   'year': 2010,
     'line_tr': 'Affet beni, ben senden başka kimseyi sevmedim',
     'line_fa': 'مرا ببخش، من جز تو کسی را دوست نداشتم'},
    {'artist': 'Ajda Pekkan',     'title': 'Petrol',                  'year': 1981,
     'line_tr': 'Petrol, petrol, petrol — para, para, para',
     'line_fa': 'نفت، نفت، نفت — پول، پول، پول'},
    {'artist': 'Aleyna Tilki',    'title': 'Sen Olsan Bari',          'year': 2017,
     'line_tr': 'Sen olsan bari, hayalim olsan bari',
     'line_fa': 'کاش لااقل تو می‌بودی، کاش لااقل خیال من می‌بودی'},
    {'artist': 'Mabel Matiz',     'title': 'Maya',                    'year': 2021,
     'line_tr': 'Bir mayam var, susulmaz bu ezgi',
     'line_fa': 'مایه‌ای دارم که این آهنگ ساکت نمی‌شود'},
    {'artist': 'Sertab Erener',   'title': 'Aşkın Bana Değen En Güzel Şey', 'year': 2009,
     'line_tr': 'Aşkın bana değen en güzel şey',
     'line_fa': 'عشقت زیباترین چیزی است که به من رسیده'},
    {'artist': 'Cem Karaca',      'title': 'Resimdeki Gözyaşları',    'year': 1977,
     'line_tr': 'Resimdeki gözyaşların hâlâ kurumaz',
     'line_fa': 'اشک‌های روی عکس هنوز خشک نمی‌شوند'},
    {'artist': 'Nilüfer',         'title': 'Erkekler de Ağlar',       'year': 1983,
     'line_tr': 'Erkekler de ağlar, görünmez gözyaşları',
     'line_fa': 'مردها هم گریه می‌کنند، فقط اشک‌هایشان دیده نمی‌شود'},
    {'artist': 'Tarkan',          'title': 'Kuzu Kuzu',               'year': 2001,
     'line_tr': 'Kuzu kuzu gelir bana yine',
     'line_fa': 'باز هم آرام و رام پیش من می‌آیی'},
    {'artist': 'Sıla',            'title': 'Boş Yere',                'year': 2014,
     'line_tr': 'Boş yere ümitlendin yine boşa',
     'line_fa': 'باز هم بیهوده امیدوار شدی، بیهوده'},
    {'artist': 'Yıldız Tilbe',    'title': 'Delikanlım',              'year': 1994,
     'line_tr': 'Delikanlım, senin için her şey kolay',
     'line_fa': 'جوانم، برای تو همه چیز آسان است'},
    {'artist': 'Edip Akbayram',   'title': 'Hasretinden Prangalar Eskittim', 'year': 1977,
     'line_tr': 'Hasretinden prangalar eskittim',
     'line_fa': 'از حسرت تو زنجیرها را فرسوده کردم'},
]
todays_song = SONG_ROTATION[now.timetuple().tm_yday % len(SONG_ROTATION)]
print(f"🎵 Song today: {todays_song['artist']} — {todays_song['title']}")


# --- 3f. PERSIAN POETRY ROTATION (evening edition — 14-day cycle) ---
# Each entry: short verses (1-2 beyts), brief translation, attribution.
POETRY_ROTATION = [
    {'poet': 'عمر خیام', 'work': 'رباعیات',
     'verses': 'این یک‌دو سه روزه نوبت عمر گذشت\nچون آب به جویبار و چون باد به دشت\nهرگز غم دو روز مرا یاد نگشت\nروزی که نیامده‌ست و روزی که گذشت',
     'translation': 'این چند روز کوتاه عمر گذشت، چون آب در جوی و باد در دشت. هرگز غم دو روز را به دل راه ندادم: روزی که هنوز نیامده، و روزی که گذشته.'},
    {'poet': 'حافظ', 'work': 'دیوان حافظ',
     'verses': 'دل می‌رود ز دستم صاحب‌دلان خدا را\nدردا که راز پنهان خواهد شد آشکارا',
     'translation': 'دلم از دست می‌رود ای صاحب‌دلان، به خاطر خدا کمک کنید — دریغ که این راز نهفته آشکار خواهد شد.'},
    {'poet': 'سعدی', 'work': 'گلستان',
     'verses': 'بنی آدم اعضای یکدیگرند\nکه در آفرینش ز یک گوهرند\nچو عضوی به درد آورد روزگار\nدگر عضوها را نماند قرار',
     'translation': 'فرزندان آدم اعضای یک پیکرند که در آفرینش از یک گوهر سرشته‌اند. چون عضوی به درد آید، اعضای دیگر آرام و قرار ندارند.'},
    {'poet': 'مولانا', 'work': 'مثنوی معنوی',
     'verses': 'بشنو از نی چون حکایت می‌کند\nاز جدایی‌ها شکایت می‌کند\nکز نیستان تا مرا ببریده‌اند\nاز نفیرم مرد و زن نالیده‌اند',
     'translation': 'از این نی بشنو که چگونه حکایت می‌کند — از جدایی‌ها شکایت می‌کند: از زمانی که مرا از نیستان بریده‌اند، فریاد من مرد و زن را به ناله انداخته است.'},
    {'poet': 'عمر خیام', 'work': 'رباعیات',
     'verses': 'ای دوست بیا تا غم فردا نخوریم\nو این یک‌دم عمر را غنیمت شمریم\nفردا که ازین دیر کهن درگذریم\nبا هفت‌هزار سالگان سر به سریم',
     'translation': 'ای دوست بیا غم فردا نخوریم و این لحظه عمر را غنیمت بدانیم. فردا که از این کاروانسرای کهن می‌گذریم، با هفت‌هزار سال‌سالگانِ خاک شده هم‌سرنوشت خواهیم بود.'},
    {'poet': 'حافظ', 'work': 'دیوان حافظ',
     'verses': 'گل در بر و می در کف و معشوق به کام است\nسلطان جهانم به چنین روز غلام است',
     'translation': 'گل در آغوش، می در دست، معشوق در کنار — در چنین روزی، سلطان جهان به نوکری من می‌نازد.'},
    {'poet': 'فروغ فرخزاد', 'work': 'تولدی دیگر',
     'verses': 'تنها صداست که می‌ماند\nدر سرزمین قدکوتاهان\nمعیارهای سنجش\nهمیشه بر مدار صفر سفر کرده‌اند',
     'translation': 'تنها صدا است که باقی می‌ماند — در سرزمین قدکوتاهان، معیارهای سنجش همیشه بر مدار صفر چرخیده‌اند.'},
    {'poet': 'سهراب سپهری', 'work': 'حجم سبز',
     'verses': 'زندگی رسم خوشایندی است\nزندگی بال و پری دارد با وسعت مرگ\nپرشی دارد اندازه عشق\nزندگی چیزی نیست که لب طاقچه عادت از یاد من و تو برود',
     'translation': 'زندگی رسم خوشایندی است؛ زندگی بال و پری دارد به پهنای مرگ، پرشی دارد به اندازه عشق. زندگی چیزی نیست که بر لب طاقچه عادت از یاد ما برود.'},
    {'poet': 'عمر خیام', 'work': 'رباعیات',
     'verses': 'هر سبزه که بر کنار جویی رسته است\nگویی ز لب فرشته خویی رسته است\nپا بر سر سبزه تا به خواری ننهی\nکان سبزه ز خاک لاله‌رویی رسته است',
     'translation': 'هر سبزه‌ای که در کنار جویی روییده، گویی از لب فرشته‌خویی سر برآورده است. پای خود را به خواری بر سبزه مگذار، که آن سبزه از خاک لاله‌رخساری روییده است.'},
    {'poet': 'احمد شاملو', 'work': 'هوای تازه',
     'verses': 'من درد مشترکم\nمرا فریاد کن\nانسان است که می‌سراید\nسرود انسان عظیم‌ترین سرود است',
     'translation': 'من دردی مشترکم، مرا فریاد کن — این انسان است که می‌سراید، و سرود انسان عظیم‌ترین سرود جهان است.'},
    {'poet': 'حافظ', 'work': 'دیوان حافظ',
     'verses': 'سال‌ها دل طلب جام جم از ما می‌کرد\nوآنچه خود داشت ز بیگانه تمنا می‌کرد',
     'translation': 'سال‌ها دل از ما جام جم را می‌طلبید — و آنچه خود در درون داشت، از بیگانه آرزو می‌کرد.'},
    {'poet': 'مولانا', 'work': 'دیوان شمس',
     'verses': 'هر روز نوگل دگری چیدن از وفاست\nروزی به یاد بود و دگر روز در صفاست\nهرکس به قدر دانش خود بهره‌ای برد\nاز این بساط که بر روی خاک ماست',
     'translation': 'هر روز چیدن گل تازه‌ای از وفاداری است — روزی به یادگار، روزی در شادی. هر کس به اندازه دانش خود از این سفره‌ای که بر روی خاک گسترده‌ایم بهره می‌برد.'},
    {'poet': 'عمر خیام', 'work': 'رباعیات',
     'verses': 'گویند که فردوس برین خواهد بود\nوآنجا می ناب و حورعین خواهد بود\nگر ما می و معشوق گزیدیم چه باک\nچون عاقبت کار همین خواهد بود',
     'translation': 'گویند که فردوس برترین خواهد بود و آنجا شراب ناب و حورعین — اگر ما در این جهان می و معشوق برگزیدیم چه باک، چون عاقبت همه به همان جا خواهیم رسید.'},
    {'poet': 'سعدی', 'work': 'بوستان',
     'verses': 'دو چیز طیره‌ی عقل است: دم فروبستن\nبه وقت گفتن و گفتن به وقت خاموشی',
     'translation': 'دو چیز سبب خفت عقل است: لب فروبستن هنگامی که باید سخن گفت، و سخن گفتن هنگامی که باید خاموش بود.'},
]
todays_poem = POETRY_ROTATION[now.timetuple().tm_yday % len(POETRY_ROTATION)]
print(f"📜 Poem today: {todays_poem['poet']} — {todays_poem['work']}")


# --- 3g. WORLD CUP 2026 COVERAGE — date-scaled article count ---
# User asked: start mellow, ramp up as the tournament reaches playoffs.
# FIFA WC 2026 calendar: June 11–July 19, 2026, US/Canada/Mexico.
def worldcup_article_count(today):
    md = (today.month, today.day)
    if md < (6, 11):  return 1   # pre-tournament — single warm-up article
    if md < (6, 28):  return 2   # group stage
    if md < (7, 9):   return 3   # Round of 16 + Quarter-finals
    return 4                      # Semis + Final — peak coverage
wc_count = worldcup_article_count(now)
# Tournament has ended (after July 20) → disable section
wc_section_enabled = (now.month, now.day) <= (7, 20)
print(f"🏆 World Cup section: {'enabled' if wc_section_enabled else 'disabled'}, "
      f"target {wc_count} article(s)")


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


def _fetch_v3_meta(url):
    """Quick fetch of og:title + og:description from a Varzesh3 article page.
    Returns the properly-punctuated headline and a one-line summary — these are
    far better than the slug-extracted title for prompting the model."""
    try:
        r = requests.get(url, headers=UA_HEADERS, timeout=10)
        if r.status_code != 200:
            return None, None
        r.encoding = 'utf-8'
        og_title = re.search(
            r'<meta[^>]+(?:property|name)="og:title"[^>]+content="([^"]+)"', r.text)
        og_desc = re.search(
            r'<meta[^>]+(?:property|name)="og:description"[^>]+content="([^"]+)"', r.text)
        title = htmllib.unescape(og_title.group(1)) if og_title else None
        desc = htmllib.unescape(og_desc.group(1)) if og_desc else None
        return title, desc
    except Exception:
        return None, None


def fetch_varzesh3_worldcup(max_items=3):
    """Scrape Varzesh3's World Cup league page for article URLs (the page is
    JS-hydrated for cards but article hrefs ARE in static HTML, ~200 per
    fetch). Then enrich each pick with og:title + og:description via a
    per-article fetch — gives the model REAL titles and summaries instead of
    just the dashed slug, which produced thin filler articles before.

    Varzesh3's RSS is frozen (2025-08-25); this page is the only live source."""
    url = ('https://www.varzesh3.com/football/league/28/'
           '%D8%AC%D8%A7%D9%85-%D8%AC%D9%87%D8%A7%D9%86%DB%8C')
    try:
        from urllib.parse import unquote
        r = requests.get(url, headers=UA_HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"   WC  ✗ Varzesh3 WC: HTTP {r.status_code}")
            return []
        r.encoding = 'utf-8'
        seen = set()
        url_list = []
        for m in re.finditer(r'/news/(\d+)/([^\s"<>]+)', r.text):
            news_id = m.group(1)
            slug = m.group(2).rstrip('"').rstrip('/').rstrip(',')
            if news_id in seen:
                continue
            seen.add(news_id)
            slug_title = unquote(slug).replace('-', ' ').strip()
            if len(slug_title) < 10:
                continue
            url_list.append((news_id, slug, slug_title))
            if len(url_list) >= max_items:
                break

        # Enrich each URL with proper og: meta — ~5 quick fetches in series
        out = []
        for news_id, slug, slug_title in url_list:
            article_url = f'https://www.varzesh3.com/news/{news_id}/{slug}'
            real_title, real_desc = _fetch_v3_meta(article_url)
            out.append({
                'title': real_title or slug_title,
                'link': article_url,
                'pub': '',
                'summary': real_desc or '',
            })
        with_summary = sum(1 for o in out if o['summary'])
        print(f"   WC  ✓ Varzesh3 World Cup: {len(out)} articles "
              f"({with_summary} with og:description summaries)")
        return out
    except Exception as e:
        print(f"   WC  ✗ Varzesh3 WC: {e}")
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

        # Sports filter: positive keywords + exclusion lists.
        # NOTE: bare "آزمون" was REMOVED — it means both "Sardar Azmoun" (the
        # footballer) AND "exam/test". It was pulling TOEFL/Duolingo/PTE
        # language-exam news into the sports section. Use "سردار آزمون" only.
        SPORTS_POS = [
            'استقلال ', 'پرسپولیس', 'سپاهان', 'تراکتور', 'فوتبال',
            'تیم ملی', 'فدراسیون فوتبال', 'فیفا', 'یوفا', 'جام جهانی',
            'لیگ برتر', 'لالیگا', 'سوپرلیگ', 'پریمیرلیگ', 'سری آ',
            'بازیکن', 'گلزن', 'سرمربی', 'کاپیتان', 'ورزشگاه', 'استادیوم',
            'کشتی فرنگی', 'کشتی آزاد', 'والیبال', 'بسکتبال', 'وزنه‌برداری',
            'تکواندو', 'کاراته', 'دو میدانی', 'شنا قهرمانی',
            'طارمی', 'سردار آزمون', 'جهانبخش', 'علی دایی', 'علی پروین',
            'نقل و انتقالات', 'مسابقه قهرمانی', 'بازی دوستانه', 'داور لیگ',
        ]
        SPORTS_NEG = [
            # maritime / military false positives for "کشتی" (=ship)
            'تنگه هرمز', 'سپاه پاسداران', 'بندرعباس', 'توقیف کشتی',
            'کشتی تجاری', 'کشتی نفتکش', 'کشتی توقیف', 'حمله به کشتی',
            # language-exam false positives for "آزمون" (=exam)
            'تافل', 'دولینگو', 'دولینگ', 'پی‌تی‌ئی', 'پی تی ئی',
            'جی‌آر‌ای', 'جی آر ای', 'آزمون زبان', 'آزمون تافل',
            'آزمون‌های', 'آزمون آنلاین', 'آزمون ورودی', 'آزمون استخدام',
        ]

        from email.utils import parsedate_to_datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        # For the sports section, drop anything older than 4 days — the general
        # IranWire feed is sparse on sport, so without this it surfaces week-old
        # items and the section reads like "same news from 3 days ago".
        max_age_days = 4 if sports_only else 30

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
            pub = extract(r'<pubDate[^>]*>(.*?)</pubDate>')
            # Recency guard — skip stale items
            if pub:
                try:
                    age = (now - parsedate_to_datetime(pub)).total_seconds() / 86400
                    if age > max_age_days:
                        continue
                except Exception:
                    pass  # unparseable date — keep the item rather than drop it
            out.append({
                'title': title,
                'link': extract(r'<link[^>]*>(.*?)</link>'),
                'pub': pub,
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

    # Italian feeds (Rome culture + politics — was a Google-Search-only black hole)
    italy_sources = [
        ('ANSA Cultura',      'https://www.ansa.it/sito/notizie/cultura/cultura_rss.xml'),
        ('ANSA Politica',     'https://www.ansa.it/sito/notizie/politica/politica_rss.xml'),
        ('Repubblica Cronaca','https://www.repubblica.it/rss/cronaca/rss2.0.xml'),
    ]
    for name, url in italy_sources:
        items = fetch_rss(url, name, max_items=5, encoding='utf-8')
        if items:
            parts.append(f"\n──── منبع: {name} (ایتالیا — RSS امروز) ────")
            for it in items:
                line = f"• «{it['title']}»"
                if it['pub']:
                    line += f"  [{it['pub']}]"
                if it['link']:
                    line += f"\n  🔗 {it['link']}"
                if it['summary']:
                    line += f"\n  📝 {it['summary']}"
                parts.append(line)

    # Spanish feeds (Barcelona local + culture — was also Google-Search-only)
    spain_sources = [
        ('La Vanguardia Barcelona', 'https://www.lavanguardia.com/rss/local/barcelona.xml'),
        ('La Vanguardia Cultura',   'https://www.lavanguardia.com/rss/cultura.xml'),
    ]
    for name, url in spain_sources:
        items = fetch_rss(url, name, max_items=5, encoding='utf-8')
        if items:
            parts.append(f"\n──── منبع: {name} (اسپانیا — RSS امروز) ────")
            for it in items:
                line = f"• «{it['title']}»"
                if it['pub']:
                    line += f"  [{it['pub']}]"
                if it['link']:
                    line += f"\n  🔗 {it['link']}"
                if it['summary']:
                    line += f"\n  📝 {it['summary']}"
                parts.append(line)

    # Turkish Süper Lig — Hürriyet sport feed
    tr_sports = fetch_rss('https://www.hurriyet.com.tr/rss/spor', 'Hürriyet Spor',
                          max_items=5, encoding='utf-8')
    if tr_sports:
        parts.append("\n──── منبع: Hürriyet Spor (Süper Lig — RSS امروز) ────")
        for it in tr_sports:
            line = f"• «{it['title']}»"
            if it['pub']:
                line += f"  [{it['pub']}]"
            if it['link']:
                line += f"\n  🔗 {it['link']}"
            if it['summary']:
                line += f"\n  📝 {it['summary']}"
            parts.append(line)

    # Local Turkish feeds — kills the "Kuşadası tourism season" recycled placeholder.
    # All three checked live as of May 2026 with daily-or-faster updates.
    local_sources = [
        ('Aydın Post',        'https://www.aydinpost.com/rss'),
        ('Kuşadası.gen.tr',   'https://www.kusadasi.gen.tr/rss'),
        ('Söke Gündem',       'https://www.sokegundem.com/rss'),
    ]
    for name, url in local_sources:
        items = fetch_rss(url, name, max_items=5, encoding='utf-8')
        if items:
            parts.append(f"\n──── منبع: {name} (محلی ترکیه — RSS امروز) ────")
            for it in items:
                line = f"• «{it['title']}»"
                if it['pub']:
                    line += f"  [{it['pub']}]"
                if it['link']:
                    line += f"\n  🔗 {it['link']}"
                if it['summary']:
                    line += f"\n  📝 {it['summary']}"
                parts.append(line)

    # World Cup 2026 — scrape Varzesh3's dedicated league page (article URLs are
    # in the static HTML even though cards are JS-hydrated). Pulls 5 articles;
    # the prompt picks N of them based on tournament phase.
    wc_items = fetch_varzesh3_worldcup(max_items=5)
    if wc_items:
        parts.append("\n──── منبع: Varzesh3 — صفحه جام جهانی ۲۰۲۶ ────")
        for it in wc_items:
            line = f"• «{it['title']}»"
            if it['link']:
                line += f"\n  🔗 {it['link']}"
            if it['summary']:
                line += f"\n  📝 {it['summary']}"
            parts.append(line)

    # European football — BBC Champions League RSS is the cleanest UEFA feed
    # (UEFA.com's own RSS was 404 on last probe). Turkish-team angle covered by
    # Hürriyet Spor + Sabah, which are already in the mix.
    eu_football = fetch_rss('https://feeds.bbci.co.uk/sport/football/champions-league/rss.xml',
                            'BBC Champions League', max_items=5, encoding='utf-8')
    if eu_football:
        parts.append("\n──── منبع: BBC Champions League (فوتبال اروپا — RSS امروز) ────")
        for it in eu_football:
            line = f"• «{it['title']}»"
            if it['pub']:
                line += f"  [{it['pub']}]"
            if it['link']:
                line += f"\n  🔗 {it['link']}"
            if it['summary']:
                line += f"\n  📝 {it['summary']}"
            parts.append(line)

    # Sabah Spor — Turkish football with detailed Turkish-team + European coverage
    sabah_items = fetch_rss('https://www.sabah.com.tr/rss/spor.xml',
                            'Sabah Spor', max_items=5, encoding='utf-8')
    if sabah_items:
        parts.append("\n──── منبع: Sabah Spor (ورزش ترکیه — RSS امروز) ────")
        for it in sabah_items:
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


# --- 4d. MORNING vs EVENING section blocks ---
# Two editions intentionally feel different:
#   MORNING — energetic, planning-the-day: Turkish word + song + recipe + Migros
#   EVENING — reflective, closing-the-day: expanded health + Persian poetry
# Recipe goes to morning because the Migros basket aligns with the day's shopping
# pattern. By evening it's too late to act on.

MORNING_SECTIONS = f"""**۱۰.** div.turkish-word — **کلمه ترکی روز** (Turkish Word of the Day):
   یک کلمه یا عبارت ترکی روزمره با ترجمه فارسی و یک مثال کوتاه. **متفاوت از ترانه روز پایین.**
   ساختار: <div class="turkish-word"> با turkish-title "★ کلمه ترکی روز ★"، turkish-main برای کلمه ترکی، turkish-meaning برای ترجمه فارسی، turkish-ex برای جمله مثال (ترکی + ترجمه فارسی).

**۱۱.** div.turkish-word (با کلاس دوم) — **ترانه ترکی روز** (Turkish Song of the Day):

   ⭐ **ترانه امروز از فهرست داخلی انتخاب شده — دقیقاً همین را بنویسید:**
   • نام ترانه: **{todays_song['title']}**
   • خواننده: **{todays_song['artist']}**
   • سال انتشار: **{todays_song['year']}**
   • مصرع ترکی: «{todays_song['line_tr']}»
   • ترجمه فارسی: «{todays_song['line_fa']}»

   ⚠️ **قانون مهم برای لینک‌ها:**
   هرگز از فرمت `https://open.spotify.com/track/<id>` استفاده نکنید — شناسه‌های track را نمی‌دانید.
   همیشه URL جستجو که در همه جا کار می‌کند:
     - Spotify: `https://open.spotify.com/search/{todays_song['artist'].replace(' ', '%20')}%20{todays_song['title'].replace(' ', '%20')}`
     - YouTube: `https://www.youtube.com/results?search_query={todays_song['artist'].replace(' ', '+')}+{todays_song['title'].replace(' ', '+')}`

   ساختار:
   <div class="turkish-word">
     <div class="turkish-title">★ ترانه ترکی روز ★</div>
     <div class="turkish-main">{todays_song['title']}</div>
     <div class="turkish-meaning">{todays_song['artist']} · {todays_song['year']}</div>
     <div class="turkish-ex">
       <strong>{todays_song['line_tr']}</strong><br>
       {todays_song['line_fa']}<br>
       <a href="https://open.spotify.com/search/{todays_song['artist'].replace(' ', '%20')}%20{todays_song['title'].replace(' ', '%20')}" target="_blank">🎧 Spotify</a> ·
       <a href="https://www.youtube.com/results?search_query={todays_song['artist'].replace(' ', '+')}+{todays_song['title'].replace(' ', '+')}" target="_blank">▶ YouTube</a>
     </div>
   </div>

**۱۲.** div.history-box — ۳ رویداد تاریخی این روز (با history-year پررنگ).

**۱۳.** div.health-tip — کوتاه (یک پاراگراف). مناسب سن ۷۰+، مرتبط با هوای امروز یا فصل.

**۱۴.** section-header green «آشپزی · دستور روز»
   **دستور امروز:** {todays_recipe['name_fa']} ({todays_recipe['name_other']})
   **راهنما / شرح کلی:** {todays_recipe['hint']}

   شما **حتماً** همین دستور را بنویسید — تنوع روزانه یک ارزش جدی این روزنامه است.
   • recipe-title: نام فارسی دستور
   • recipe-heading «📌 اجزا»: فهرست دقیق مواد لازم برای ۴ نفر
   • recipe-heading «🧑‍🍳 طرز تهیه»: مراحل شماره‌گذاری شده (۶ تا ۸ مرحله)
   • recipe-heading «💚 یادداشت سلامتی»: یک پاراگراف کوتاه درباره ارزش غذایی برای سن ۷۰+

   ⛔ **اکیداً ممنوع:** سوپ عدس قرمز (Mercimek Çorbası).

**۱۵.** div.migros-box — مواد لازم **همان دستور بالا ({todays_recipe['name_fa']})** با قیمت‌های روز.
   **دقت قیمت — مهم:**
   تاریخ امروز **{today_human_en}** است. لیر ترکیه در یک سال گذشته به‌شدت ضعیف شده و قیمت‌ها هر ماه تغییر می‌کنند. **از قیمت‌های ۲۰۲۵ یا قبل از ۲۰۲۶ استفاده نکنید** — قیمت‌ها باید مربوط به **ماه فعلی ({today_str})** باشند.

   راهنمای سطح قیمت میگروس برای ژوئن ۲۰۲۶ (تقریبی):
   • نان (۱ قرص): ۱۵-۲۰ ₺
   • تخم‌مرغ (۱۰ عددی): ۱۲۰-۱۵۰ ₺
   • گوشت گوساله (۱ کیلو): ۸۵۰-۱،۰۵۰ ₺
   • مرغ (۱ کیلو): ۱۸۰-۲۲۰ ₺
   • شیر (۱ لیتر): ۵۰-۶۵ ₺
   • گوجه‌فرنگی (۱ کیلو): ۴۰-۶۰ ₺ (فصلی)
   • بادمجان (۱ کیلو): ۳۵-۵۰ ₺ (تابستان ارزان‌تر)
   • پنیر سفید (۲۵۰ گرم): ۱۰۰-۱۳۰ ₺
   • روغن زیتون (۵۰۰ میل): ۲۰۰-۲۸۰ ₺
   • برنج (۱ کیلو): ۸۰-۱۱۰ ₺
   • سیر (۱۰۰ گرم): ۲۵-۳۵ ₺
   • پیاز (۱ کیلو): ۲۰-۳۰ ₺

   **اگر قیمت دقیق نمی‌دانید، از این محدوده‌ها استفاده کنید — قیمت میانگین را بنویسید.** هرگز قیمت‌های زیر این محدوده ننویسید (نشانه قیمت قدیمی است).

   در migros-total بنویسید: «قیمت‌ها تقریبی برای ژوئن ۲۰۲۶ — ممکن است در فروشگاه تا ۱۵٪ متفاوت باشد.»"""

EVENING_SECTIONS = f"""**۱۰.** div.history-box — ۳ رویداد تاریخی این روز (با history-year پررنگ).

**۱۱.** div.health-tip — **نسخه عصر: گسترش یافته (۲ پاراگراف).**
   - پاراگراف اول: یک نکته بهداشتی مشخص و عملی برای شب — مثلاً تکنیک تنفس برای خواب بهتر، حرکت کششی قبل از خواب، چای گیاهی مفید (نام ببرید: بابونه، گل گاوزبان، آویشن)، یا توصیه‌ای درباره مصرف آب در شب.
   - پاراگراف دوم: یک تذکر کوچک‌تر — مثلاً درباره دارو شبانه، ساعت خواب، یا یک ورزش سبک.
   مناسب سن ۷۰+ و مرتبط با هوای امروز یا فصل.

**۱۲.** section-header gold «شعر شبانه» (Evening Poetry)
   div.poetry-box با شعر فارسی منتخب امروز:
   • **شاعر امروز: {todays_poem['poet']}** — از *{todays_poem['work']}*
   • **ابیات:**
     {todays_poem['verses']}
   • **توضیح کوتاه فارسی (نه ترجمه — فقط شرح حال):** {todays_poem['translation']}

   ساختار دقیق:
   <div class="poetry-box">
     <div class="poetry-title">★ شعر شبانه ★</div>
     <div class="poetry-verses">[ابیات با <br> بین مصرع‌ها]</div>
     <div class="poetry-translation">[شرح کوتاه]</div>
     <div class="poetry-attribution">— {todays_poem['poet']} · {todays_poem['work']} —</div>
   </div>

**۱۳.** بسط یک یا دو مقاله از بخش‌های خبر (ایران/جهان یا گزارش از رم):
   در نسخه عصر، یکی از مقالات بخش‌های قبل (Iran/Rome/Barcelona/local) را با یک **پاراگراف تحلیلی اضافی** گسترش دهید — این پاراگراف بعد از پاراگراف‌های اصلی مقاله اضافه می‌شود (نه به‌عنوان مقاله جدید). محتوای پاراگراف تحلیلی: زمینه تاریخی، تأثیر بر منطقه، یا پیامد محتمل.
   • برای این کار، در مقاله انتخابی، یک پاراگراف چهارم با کلاس معمولی <p> اضافه کنید که شروع آن «در تحلیل خبر:» باشد.
   • فقط **یک یا دو** مقاله را گسترش دهید — نه همه.

⛔ **در نسخه عصر این بخش‌ها وجود ندارد:** آشپزی، میگروس، کلمه ترکی، ترانه ترکی. آن‌ها در نسخه صبح هستند."""


is_morning = (edition_en == "Morning")
morning_or_evening_specific_sections = MORNING_SECTIONS if is_morning else EVENING_SECTIONS

# World Cup section — appears between section 4 (sports) and section 5 (local).
# Number of articles scales with tournament phase (see worldcup_article_count).
if wc_section_enabled:
    worldcup_section = f"""**۴ب.** section-header gold «جام جهانی ۲۰۲۶» (World Cup News)
   ⭐ **منبع اصلی: Varzesh3 — صفحه جام جهانی ۲۰۲۶ از فهرست بالا.**
   **تعداد مقاله امروز: دقیقاً {wc_count}** (بر اساس فاز فعلی جام جهانی).

   **اولویت‌بندی انتخاب از فید Varzesh3:**
   ۱. **اولویت ۱ — هر خبر مربوط به ترکیه یا ایران در جام جهانی** (تیم ملی ترکیه/ایران، حذف، صعود، اظهارات بازیکنان ترکی/ایرانی، Güler, طارمی, آزمون, جهانبخش).
      چون این روزنامه برای جامعه فارسی‌زبان در ترکیه است، خبر ترکیه/ایران در جام جهانی بسیار مهم‌تر از خبر اسپانیا یا برزیل است.
   ۲. اولویت ۲ — خبر بزرگ تیم‌های مدعی (برزیل، آرژانتین، فرانسه، اسپانیا، آلمان).
   ۳. اولویت ۳ — تحلیل، آمار، یا اخبار حاشیه‌ای جالب.

   **کیفیت هر مقاله — ساختار:**
   • h2.lead: تیتر واقعی پس از «•» در فید (نه از slug؛ نه دست‌کاری).
   • h3.deck: خلاصه پس از «📝» در فید.
   • **پاراگراف اصلی (۲ تا ۳ پاراگراف کامل):**
     - پاراگراف ۱: گسترش خلاصه، با اضافه کردن زمینه (چه تیم‌ها، چه ساعت، چه رتبه‌ای، چه نتیجه‌ای).
     - پاراگراف ۲ (اختیاری): تأثیر، واکنش، یا چشم‌انداز بعدی (بازی بعدی، احتمال صعود، حال‌و‌هوای هواداران).
     - پاراگراف ۳ (اختیاری): یک نقل قول یا نکته جالب از خبر اصلی.
   • blockquote (اختیاری): اگر در خلاصه نقل قول مستقیم هست.
   • byline-row با لینک قابل کلیک:
     <div class="byline-row">
       <span class="name">به نقل از <a href="[URL واقعی از فید]" target="_blank">Varzesh3</a>، {today_str}</span>
     </div>

   ⛔ **پرهیز از تکرار:** اگر خبری در بخش ۶ (ورزش محلی ترکیه) از Hürriyet Spor می‌نویسید، در این بخش از خبر یکسان استفاده نکنید. WC و Local Turkish Sports نباید همان داستان را تکرار کنند."""
else:
    worldcup_section = ""  # tournament finished, skip section
closing_tone = (
    "صبح است — لحن گرم، انگیزه‌بخش، آغاز روز. ۲ تا ۳ جمله."
    if is_morning
    else "عصر است — لحن آرام، شاعرانه، خاتمه روز. مرتبط با یکی از تیترهای امروز یا با حال‌و‌هوای فصل. ۳ تا ۵ جمله."
)


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
   ۱ تا ۲ مقاله. ⭐ **منبع اصلی و اولویت اول: khabarvarzeshi** — این فید هر روز چند بار به‌روز می‌شود و تازه‌ترین است. IranWire (ورزش) فقط مکمل است.

   ⛔ **اکیداً ممنوع: خبرگزاری Varzesh3** (فید از مرداد ۱۴۰۴ مرده است).

   **قانون تازگی (مهم — این بخش قبلاً خبر ۳ روز پیش را تکرار می‌کرد):**
   • فقط از تیترهایی استفاده کنید که تاریخشان **در ۲ روز اخیر** است. تاریخ هر تیتر در فهرست بالا کنار آن آمده (`[Sat, 05 Sep 2026 ...]`). تیتر قدیمی‌تر از ۲ روز را **کامل نادیده بگیرید**.
   • تیترهای khabarvarzeshi تقریباً همیشه از امروز هستند — از آن‌ها شروع کنید.
   • **هرگز همان خبری را که احتمالاً دیروز نوشته شده تکرار نکنید** — تیتر متفاوت و تازه انتخاب کنید.

   محتوای قابل قبول (از تیترهای تازه):
   • نتیجه بازی هفته جاری لیگ برتر، گلزنان، جدول
   • نقل و انتقالات یا اعلامیه باشگاه/فدراسیون
   • ستاره‌های ایرانی در لیگ‌های خارجی (طارمی، جهانبخش، سردار آزمون)
   • استقلال، پرسپولیس، سپاهان، تراکتور
   • کشتی، والیبال، بسکتبال، تکواندو
   **byline حتماً نام منبع واقعی (khabarvarzeshi.com یا IranWire) + URL واقعی از فهرست بالا.**

{worldcup_section}

**۴ج.** section-header gold «فوتبال اروپا» (European Football)
   ۱ مقاله در روز. ⭐ **منابع اصلی: BBC Champions League + Sabah Spor + Hürriyet Spor از فهرست بالا.**

   **اولویت انتخاب مقاله (به این ترتیب):**
   ۱. **تیم‌های ترکیه در اروپا** (Galatasaray, Fenerbahçe, Beşiktaş, Trabzonspor) در Champions League/Europa League/Conference League — نتیجه بازی، قرعه‌کشی، پیش‌نمایش، انتقال بازیکن با نام و تیم مقصد اروپایی.
   ۲. قرعه‌کشی جدید، جدول لیگ قهرمانان، گروه‌بندی، تحلیل بازی‌های هفته.
   ۳. اخبار مهم تیم‌های بزرگ اروپا (Real Madrid, Barcelona, PSG, Man City, Bayern, Inter, Milan, Napoli, Chelsea, Arsenal, Liverpool) با تمرکز بر بازی‌های آینده.

   **کیفیت مقاله:**
   • h2.lead: تیتر واقعی از فید (نه ترجمه ماشینی — از ترکی/انگلیسی به فارسی روان بازنویسی کنید).
   • h3.deck: خلاصه از فید، ترجمه‌شده.
   • ۲ پاراگراف کامل: پاراگراف ۱ خبر اصلی، پاراگراف ۲ زمینه یا تأثیر (مثلاً «Galatasaray در گروه E با PSG و Real Madrid همگروه شد»).
   • byline-row با لینک قابل کلیک به منبع اصلی:
     <div class="byline-row">
       <span class="name">به نقل از <a href="[URL از فید]" target="_blank">BBC Champions League</a> یا Hürriyet Spor یا Sabah Spor، {today_str}</span>
     </div>

   **پرهیز از تکرار:** اگر خبری در بخش ۶ (ورزش محلی ترکیه) بازتاب یافته، همان خبر را در این بخش تکرار نکنید. اگر تیم ترکیه در بحث اروپایی است، در این بخش (اروپا) بنویسید و در بخش ۶ به Süper Lig یا دیگر ورزش‌های ترکیه اختصاص دهید.

**۵.** section-header «اخبار محلی · کوشاداسی، سوکه، آیدین»
   **دقیقاً ۳ مقاله.** ⭐ **منبع اصلی: تیترهای امروز Aydın Post, Kuşadası.gen.tr, Söke Gündem از فهرست بالا** — این سه فید زنده هستند و هر روز خبرهای متفاوت دارند. **نسخه قدیمی یا کلی ننویسید** — هر مقاله باید از تیتر واقعی یکی از این سه فید گرفته شود، با URL واقعی در byline.

   محتوای قابل قبول بسیار وسیع است:

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
   ۱ مقاله. ⭐ **منبع اصلی: تیترهای امروز Hürriyet Spor از فهرست بالا** (فید زنده، روزانه چندین به‌روزرسانی).

   ⛔ **اکیداً ممنوع: خبرهای تیم ملی ترکیه در جام جهانی ۲۰۲۶.** اگر بخش ۴ب (جام جهانی) فعال است، خبرهای تیم ملی ترکیه در WC به آن بخش می‌روند، نه اینجا. این بخش فقط برای محتوای **غیر-جام-جهانی** ترکیه است.

   محتوای قابل قبول:
   • نتیجه بازی Süper Lig (Galatasaray, Fenerbahçe, Beşiktaş, Trabzonspor) با امتیاز و گلزن
   • وضعیت جدول لیگ یا تیم در رقابت‌های اروپایی (UEFA, Champions League, Europa League)
   • پیش‌نمایش بازی آخر هفته با تاریخ و ساعت
   • نقل و انتقالات تابستانی با نام بازیکن
   • والیبال، بسکتبال، یا ورزش‌های دیگر باشگاهی ترکیه

   **byline حتماً Hürriyet Spor + URL واقعی از فهرست بالا.**
   اگر تنها خبرهای Hürriyet Spor درباره جام جهانی هستند، یک محتوای جایگزین از Süper Lig یا UEFA استفاده کنید (یا از Google Search استفاده کنید).

**۷.** section-header blue «گزارش از رم»
   **دقیقاً ۲ مقاله. فوتبال اکیداً ممنوع.**
   ⭐ **منبع اصلی: تیترهای امروز ANSA و Repubblica از فهرست بالا** — این فیدها چندین بار در روز به‌روزرسانی می‌شوند.

   • مقاله ۷.۱ — **فرهنگی** (از فید ANSA Cultura):
     - نمایشگاه، اپرا، فستیوال، باستان‌شناسی، فیلم، تئاتر در رم/ایتالیا
     - نام مکان مشخص (موزه، تئاتر، گالری) + تاریخ
     - byline حتماً ANSA + URL واقعی

   • مقاله ۷.۲ — **سیاسی** (از فید ANSA Politica یا Repubblica Cronaca):
     - اعلامیه دولت ملونی، پارلمان، رای، قانون جدید
     - دیدار دیپلماتیک، رابطه با EU/USA
     - اعتراض یا رویداد سیاسی
     - byline حتماً ANSA Politica یا La Repubblica + URL واقعی

**۸.** section-header green «بارسلونا · فرهنگ»
   **دقیقاً ۱ مقاله — فقط فرهنگی. FC Barcelona و فوتبال اکیداً ممنوع.**
   ⭐ **منبع اصلی: تیترهای امروز La Vanguardia Cultura و La Vanguardia Barcelona از فهرست بالا** (فیدهای روزانه، روزنامه بزرگ کاتالان).

   محتوای قابل قبول از این فیدها:
   • نمایشگاه در Museu Picasso, MACBA, MNAC, CCCB, CaixaForum با تاریخ
   • کنسرت در Palau de la Música Catalana یا L'Auditori
   • نمایش در Liceu (اپرا)
   • معماری گاودی، Sagrada Família، Park Güell — رویداد یا کارگاه رستوراسیون
   • فستیوال (Sónar, Primavera Sound, Mercé) با تاریخ مشخص
   • رستوران، مد، طراحی، یا هنر معاصر کاتالان

   **byline حتماً La Vanguardia + URL واقعی از فهرست بالا.**
   اگر فقط خبر فوتبال در فیدها بود، از Google Search برای محتوای فرهنگی استفاده کنید.

**۹.** section-header blue «آب و هوا»
   div.box: weather-grid (۳ روز کوشاداسی) + city-weather (کوشاداسی، رم، بارسلونا). دما و وضعیت دقیق.

{morning_or_evening_specific_sections}

**[N-2].** div.closing — پیام پایانی. {closing_tone}

**[N-1].** div.footer — colophon، فهرست منابع امروز (نام دقیق رسانه‌هایی که واقعاً استفاده شده‌اند، نه فهرست عمومی)، تاریخ شماره بعدی. **بدون ایمیل، بدون آدرس وب، بدون «info@» یا «https».**

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
