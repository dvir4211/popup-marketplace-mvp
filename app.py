"""
Pop-up Space Marketplace - MVP (v3, mobile-first fixed)
Run:  pip install "streamlit>=1.39"  &&  streamlit run app.py
"""
import base64
import hmac
import html
import io
import json
import math
import re
import uuid
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

import streamlit as st

# ----------------------------------------------------------------------------
# Config & constants
# ----------------------------------------------------------------------------
st.set_page_config(page_title="פופ-אפ בשטח", page_icon="🛍️", layout="wide")

DATA_FILE = Path("spaces.json")
PLATFORM_FEE = 0.12
ADMIN_PASSWORD = "dvir2026"
DAVIR_WHATSAPP = "9725XXXXXXXX"
MAX_IMAGES = 5
HERO_IMAGE = "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1800&q=80"
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1445116572660-236099ec97a0?auto=format&fit=crop&w=900&q=80"

PERIODS = ["לשעה", "ליום", "לסופ״ש", "לשבוע", "לחודש"]
PERIOD_PLURAL = {"לשעה": "שעות", "ליום": "ימים", "לסופ״ש": "סופי שבוע", "לשבוע": "שבועות", "לחודש": "חודשים"}

# ----------------------------------------------------------------------------
# Styling: Mobile-safe RTL & Warm Aesthetics
# ----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;800&display=swap');
:root { --crimson:#B3202E; --crimson-dark:#8E1823; --bg:#FBF8F4; --text:#2F2F33; --muted:#7A7A80; }

#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
[data-testid="stDeployButton"] {display:none;}
[data-testid="stHeader"] {background:transparent;}

/* RTL applied ONLY to inner content elements to keep mobile drawer functional */
.block-container, [data-testid="stSidebarContent"], [data-testid="stMarkdownContainer"], 
label, p, h1, h2, h3, h4, li, input, textarea, .stTabs [data-baseweb="tab-list"], [data-testid="stExpander"] summary {
    direction: rtl; 
    text-align: right; 
    font-family: 'Heebo', sans-serif !important; 
    color: var(--text);
}

.stApp { background:var(--bg); }
.block-container { padding-top:2rem !important; }
[data-testid="stSidebar"] { background:#fff; box-shadow:-4px 0 24px rgba(0,0,0,.05); border: none !important; }
[data-testid="stSlider"] > div { direction:ltr; }
[data-testid="stSlider"] label { direction:rtl; text-align:right; }

@media (min-width: 769px) { 
    [data-testid="stAppViewContainer"] { flex-direction:row-reverse; } 
}

/* Buttons */
button[kind^="primary"], [data-testid^="stBaseButton-primary"], [data-testid="stBaseLinkButton-primary"] {
    background:var(--crimson) !important; border:none !important; color:#fff !important; width:100%;
    border-radius:12px !important; font-weight:700 !important; box-shadow:0 6px 16px rgba(179,32,46,.25);
    transition:all .2s ease;
}
button[kind^="primary"]:hover, [data-testid^="stBaseButton-primary"]:hover, [data-testid="stBaseLinkButton-primary"]:hover {
    background:var(--crimson-dark) !important; transform:translateY(-1px);
}
[data-testid="stBaseLinkButton-primary"] p { color:#fff !important; text-align:center; }
[data-testid="stBaseButton-secondary"] { border-radius:12px; width:100%; }

/* Cards */
[class*="st-key-card_"] {
    background:#fff; border-radius:18px; padding:14px; border:1px solid #F1EBE4;
    box-shadow:0 8px 28px rgba(60,40,30,.08); transition:transform .2s ease, box-shadow .2s ease;
}
[class*="st-key-card_"]:hover { transform:translateY(-3px); box-shadow:0 14px 34px rgba(60,40,30,.14); }
[class*="st-key-card_"] img { height:210px; object-fit:cover; border-radius:12px; }
.st-key-details_box img { max-height:460px; object-fit:cover; border-radius:18px; box-shadow:0 10px 30px rgba(0,0,0,.12); }
[data-testid="stForm"] { background:#fff; border-radius:18px; border:1px solid #F1EBE4; box-shadow:0 8px 28px rgba(60,40,30,.06); }

.card-title { font-size:1.25rem; font-weight:800; margin:8px 0 4px; }
.card-meta { color:var(--muted); font-size:.95rem; margin-bottom:2px; }
.price { color:var(--crimson); font-size:1.5rem; font-weight:800; margin:8px 0 10px; }
.price span { color:var(--muted); font-size:.9rem; font-weight:500; }
.badge {
    display:inline-block; background:linear-gradient(135deg,#FF9F1C,#E4572E); color:#fff !important;
    padding:6px 12px; border-radius:999px; font-weight:700; font-size:.85rem; margin:4px 0;
    box-shadow:0 4px 12px rgba(228,87,46,.35);
}
.quote { background:#fff; border-radius:16px; padding:16px 20px; border:1px solid #F1EBE4; box-shadow:0 8px 28px rgba(60,40,30,.06); margin-bottom:14px; }
.quote .old { text-decoration:line-through; color:var(--muted); font-size:1.15rem; }
.quote .new { color:var(--crimson); font-weight:800; font-size:1.8rem; }
.quote .hint { color:#B35C00; font-weight:500; margin-top:6px; }

/* Hero */
.hero {
    height:340px; border-radius:22px; margin-bottom:14px; display:flex; align-items:flex-end;
    background:linear-gradient(to top, rgba(30,15,15,.65), rgba(30,15,15,.05)), url('__HERO__') center/cover;
    box-shadow:0 14px 40px rgba(60,40,30,.2);
}
.hero-text { padding:28px 34px; }
.hero-text h1 { color:#fff !important; font-size:2.6rem; font-weight:800; margin:0; }
.hero-text p { color:#f3e9e2 !important; font-size:1.15rem; margin:4px 0 0; }

/* Marquee */
.marquee { direction:ltr; overflow:hidden; white-space:nowrap; background:#fff; border-radius:14px; padding:12px 0;
    margin-bottom:26px; border:1px solid #F1EBE4; box-shadow:0 4px 14px rgba(0,0,0,.05); }
.marquee span { display:inline-block; padding-left:100%; font-weight:700; color:var(--crimson); animation:marquee 16s linear infinite; }
@keyframes marquee { 0% {transform:translateX(0);} 100% {transform:translateX(-100%);} }

/* Empty state */
.empty-state { text-align:center; background:#fff; border-radius:22px; padding:60px 24px;
    box-shadow:0 10px 34px rgba(60,40,30,.08); border:1px dashed #E6D6CC; }
.empty-state .icon { font-size:3.4rem; }
.empty-state h2 { color:var(--crimson); text-align:center; margin:10px 0 6px; font-weight:800; }
.empty-state p { color:var(--muted); text-align:center; font-size:1.1rem; }

/* Mobile optimization */
@media (max-width: 768px) {
    .block-container { padding:1rem .8rem 3rem !important; }
    .hero { height:210px; border-radius:16px; }
    .hero-text { padding:16px 18px; }
    .hero-text h1 { font-size:1.6rem; }
    .hero-text p { font-size:.95rem; }
    .marquee { margin-bottom:16px; padding:9px 0; font-size:.9rem; }
    [class*="st-key-card_"] img { height:180px; }
    .st-key-details_box img { max-height:300px; }
    .quote .new { font-size:1.5rem; }
    [data-testid="stSidebar"] { min-width: 260px !important; }
    [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; gap:1rem !important; }
    [data-testid="stColumn"], [data-testid="column"] { min-width:100% !important; flex:1 1 100% !important; width:100% !important; }
}
</style>
""".replace("__HERO__", HERO_IMAGE)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Data layer
# ----------------------------------------------------------------------------
def normalize(space: dict) -> dict:
    space.setdefault("price_period", "לסופ״ש")
    space.setdefault("discount_threshold", 0)
    space.setdefault("discount_percentage", 0)
    space.setdefault("images", [])
    space.setdefault("open_hours", "-")
    space.setdefault("store_type", "")
    return space

def load_spaces() -> list[dict]:
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return [normalize(s) for s in data] if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def save_spaces(spaces: list[dict]) -> None:
    DATA_FILE.write_text(json.dumps(spaces, ensure_ascii=False, indent=1), encoding="utf-8")

def encode_image(uploaded) -> str:
    raw = uploaded.getvalue()
    try:
        from PIL import Image, ImageOps
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
        img.thumbnail((1280, 1280))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=82, optimize=True)
        raw = buf.getvalue()
    except Exception:
        pass
    return base64.b64encode(raw).decode("ascii")

@st.cache_data(show_spinner=False)
def decode_image(b64: str) -> bytes:
    return base64.b64decode(b64)

def get_images(space: dict) -> list:
    imgs = [decode_image(b) for b in space["images"]]
    return imgs or [space.get("image_url") or FALLBACK_IMAGE]

# ----------------------------------------------------------------------------
# Pricing logic
# ----------------------------------------------------------------------------
def half_up(x: float) -> int:
    return int(x + 0.5)

def display_price(space: dict) -> int:
    return half_up(space["host_price"] * (1 + PLATFORM_FEE))

def requested_days(start: date, end: date) -> int:
    return max(0, (end - start).days + 1)

def daily_hours(open_hours: str) -> int:
    m = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", open_hours)
    if not m:
        return 8
    h1, m1, h2, m2 = map(int, m.groups())
    minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
    return max(1, math.ceil((minutes if minutes > 0 else minutes + 1440) / 60))

def periods_for(space: dict, days: int) -> int:
    p = space["price_period"]
    if p == "לשעה":
        return days * daily_hours(space["open_hours"])
    if p == "ליום":
        return days
    if p == "לסופ״ש":
        return math.ceil(days / 2)
    if p == "לשבוע":
        return math.ceil(days / 7)
    return math.ceil(days / 30)

def has_discount(space: dict) -> bool:
    return space["discount_threshold"] > 0 and space["discount_percentage"] > 0

def discount_badge_text(space: dict) -> str:
    return (f"🎁 {space['discount_percentage']}% הנחה להזמנה של "
            f"{space['discount_threshold']} {PERIOD_PLURAL[space['price_period']]} ומעלה!")

def compute_quote(space: dict, start: date, end: date) -> dict:
    days = requested_days(start, end)
    periods = periods_for(space, days) if days else 0
    original = display_price(space) * periods
    qualifies = has_discount(space) and periods >= space["discount_threshold"]
    final = half_up(original * (1 - space["discount_percentage"] / 100)) if qualifies else original
    return {"days": days, "periods": periods, "original": original, "final": final, "qualifies": qualifies}

# ----------------------------------------------------------------------------
# Router State
# ----------------------------------------------------------------------------
st.session_state.setdefault("view", "catalog")
st.session_state.setdefault("selected_id", None)
st.session_state.setdefault("wa_url", None)

def open_details(space_id: str) -> None:
    st.session_state.update(view="details", selected_id=space_id, wa_url=None)

def back_to_catalog() -> None:
    st.session_state.update(view="catalog", selected_id=None, wa_url=None)

# ----------------------------------------------------------------------------
# Sidebar components
# ----------------------------------------------------------------------------
def next_friday(today: date) -> date:
    return today + timedelta(days=(4 - today.weekday()) % 7)

def render_filters(spaces: list[dict]) -> dict:
    start_default = next_friday(date.today())
    f = {"start": start_default, "end": start_default + timedelta(days=1), "hoods": [], "types": [], "budget": 10**9}
    if not spaces:
        return f

    st.header("🔎 סינון תוצאות")
    f["start"] = st.date_input("תאריך התחלה", value=start_default, min_value=date.today())
    f["end"] = st.date_input("תאריך סיום", value=start_default + timedelta(days=1), min_value=date.today())
    if f["end"] < f["start"]:
        st.error("תאריך הסיום חייב להיות אחרי תאריך ההתחלה")

    f["hoods"] = st.multiselect("אזור", sorted({s["neighborhood"] for s in spaces}), placeholder="כל האזורים")
    types = sorted({s["store_type"] for s in spaces if s["store_type"]})
    f["types"] = st.multiselect("סוג עסק", types, placeholder="כל סוגי העסקים")

    top = max(50, -(-max(display_price(s) for s in spaces) // 50) * 50)
    f["budget"] = st.slider("תקציב מקסימלי (₪)", 0, top, top, step=50)
    st.caption("התקציב מושווה למחיר ליחידת התמחור של כל חלל")
    return f

def render_admin_panel(spaces: list[dict]) -> None:
    with st.expander("ניהול מערכת (Admin)"):
        if msg := st.session_state.pop("flash", None):
            st.success(msg)

        pwd = st.text_input("סיסמה", type="password", key="admin_pwd")
        if not pwd:
            return
        if not hmac.compare_digest(pwd.encode(), ADMIN_PASSWORD.encode()):
            st.error("סיסמה שגויה")
            return

        st.markdown("**➕ הוספת חלל חדש**")
        with st.form("admin_add_form", clear_on_submit=True):
            title = st.text_input("שם החלל")
            hood = st.text_input("אזור / שכונה")
            store_type = st.text_input("סוג עסק")
            sqm = st.number_input("שטח (מ״ר)", min_value=1, value=4, step=1)
            hours = st.text_input("שעות פעילות", placeholder="08:00-16:00")
            host_price = st.number_input("מחיר מארח (₪)", min_value=0, value=500, step=10)
            period = st.selectbox("תקופת תמחור", PERIODS, index=1)
            threshold = st.number_input("מינימום תקופות להנחה (0 = ללא הנחה)", min_value=0, value=0, step=1)
            pct = st.number_input("אחוז הנחה", min_value=0, max_value=90, value=0, step=5)
            files = st.file_uploader(f"תמונות (עד {MAX_IMAGES})", type=["jpg", "jpeg", "png"],
                                     accept_multiple_files=True)
            if st.form_submit_button("הוסף חלל", type="primary"):
                if not (title.strip() and hood.strip() and store_type.strip()):
                    st.error("יש למלא שם, אזור וסוג עסק")
                elif (threshold > 0) != (pct > 0):
                    st.error("להגדרת הנחה יש למלא גם מינימום תקופות וגם אחוז הנחה")
                else:
                    spaces.append({
                        "id": uuid.uuid4().hex[:8], "title": title.strip(), "neighborhood": hood.strip(),
                        "store_type": store_type.strip(), "sqm": int(sqm), "open_hours": hours.strip() or "-",
                        "host_price": int(host_price), "price_period": period,
                        "discount_threshold": int(threshold), "discount_percentage": int(pct),
                        "images": [encode_image(f) for f in files[:MAX_IMAGES]],
                    })
                    save_spaces(spaces)
                    st.session_state.flash = "החלל נוסף בהצלחה ✅"
                    st.rerun()

        if spaces:
            st.divider()
            st.markdown("**🗑️ מחיקת חלל**")
            target = st.selectbox("בחר חלל למחיקה", spaces, format_func=lambda s: f"{s['title']} ({s['neighborhood']})")
            confirm = st.checkbox("אני מאשר מחיקה")
            if st.button("מחק חלל", disabled=not confirm):
                save_spaces([s for s in spaces if s["id"] != target["id"]])
                st.session_state.flash = "החלל נמחק ✅"
                st.rerun()

# ----------------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------------
def price_html(space: dict) -> str:
    return f'<div class="price">{display_price(space):,} ₪ <span>/ {space["price_period"].lstrip("ל")}</span></div>'

def render_hero_and_marquee() -> None:
    st.markdown(
        """
        <div class="hero"><div class="hero-text">
            <h1>פופ-אפ בשטח</h1>
            <p>החללים הכי שווים למותגי אופנה – בתוך בתי קפה וחנויות אהובים</p>
        </div></div>
        <div class="marquee"><span>🔥 בקרוב חנויות וחללים נוספים... הישארו מעודכנים! 🔥</span></div>
        """,
        unsafe_allow_html=True,
    )

def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="icon">✨</div>
            <h2>הקטלוג שלנו בהקמה</h2>
            <p>אנחנו בוחרים בקפידה את החללים הטובים ביותר עבורכם.<br>
            חללים חדשים יתווספו בקרוב – חזרו לכאן בימים הקרובים!</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_catalog(spaces: list[dict], f: dict) -> None:
    render_hero_and_marquee()
    if not spaces:
        render_empty_state()
        return

    results = [s for s in spaces
               if (not f["hoods"] or s["neighborhood"] in f["hoods"])
               and (not f["types"] or s["store_type"] in f["types"])
               and display_price(s) <= f["budget"]]

    st.subheader(f"נמצאו {len(results)} חללים")
    if not results:
        st.info("לא נמצאו חללים התואמים את הסינון. נסו להרחיב את החיפוש.")
        return

    per_row = 3
    for i in range(0, len(results), per_row):
        for col, s in zip(st.columns(per_row), results[i:i + per_row]):
            with col, st.container(key=f"card_{s['id']}"):
                st.image(get_images(s)[0], use_container_width=True)
                badge = f'<div class="badge">{html.escape(discount_badge_text(s))}</div>' if has_discount(s) else ""
                st.markdown(
                    f"""<div class="card-title">{html.escape(s['title'])}</div>
                    <div class="card-meta">📍 {html.escape(s['neighborhood'])} · {html.escape(s['store_type'])}</div>
                    <div class="card-meta">📐 {s['sqm']} מ״ר · 🕒 {html.escape(s['open_hours'])}</div>
                    {price_html(s)}{badge}""",
                    unsafe_allow_html=True,
                )
                st.button("לפרטים והרשמה", key=f"btn_{s['id']}", type="primary",
                          on_click=open_details, args=(s["id"],))

def render_quote(space: dict, q: dict) -> None:
    if q["days"] == 0:
        st.error("טווח התאריכים אינו תקין - תקנו אותו בתפריט הצד")
        return
    unit = PERIOD_PLURAL[space["price_period"]]
    if q["qualifies"]:
        total = (f'<span class="old">{q["original"]:,} ₪</span> &nbsp; <span class="new">{q["final"]:,} ₪</span>'
                 f'<div class="badge">🎉 חסכתם {q["original"] - q["final"]:,} ₪ ({space["discount_percentage"]}% הנחה)</div>')
    else:
        total = f'<span class="new">{q["final"]:,} ₪</span>'
    hint = ""
    if has_discount(space) and not q["qualifies"]:
        missing = space["discount_threshold"] - q["periods"]
        hint = f'<div class="hint">💡 הזמינו עוד {missing} {unit} וקבלו {space["discount_percentage"]}% הנחה</div>'
    st.markdown(
        f"""<div class="quote">
            <div>📅 {q['days']} ימים מבוקשים · {q['periods']} {unit} × {display_price(space):,} ₪</div>
            <div style="margin-top:6px">סה״כ לתשלום: {total}</div>{hint}
        </div>""",
        unsafe_allow_html=True,
    )

def build_whatsapp_url(space: dict, q: dict, brand: str, insta: str, phone: str, f: dict) -> str:
    lines = [
        "שלום דביר, אשמח לשריין חלל פופ-אפ 🙌",
        f"חלל: {space['title']} ({space['neighborhood']})",
        f"תאריכים: {f['start']:%d/%m/%Y} - {f['end']:%d/%m/%Y} ({q['days']} ימים)",
        f"מחיר: {display_price(space):,} ₪ {space['price_period']} × {q['periods']} {PERIOD_PLURAL[space['price_period']]}",
    ]
    if q["qualifies"]:
        lines.append(f"הנחה: {space['discount_percentage']}% (במקום {q['original']:,} ₪)")
    lines += [f"סה״כ לתשלום: {q['final']:,} ₪", f"מותג: {brand}", f"אינסטגרם: {insta}", f"טלפון: {phone}"]
    return f"https://wa.me/{DAVIR_WHATSAPP}?text={quote(chr(10).join(lines))}"

def render_details(spaces: list[dict], f: dict) -> None:
    space = next((s for s in spaces if s["id"] == st.session_state.selected_id), None)
    if space is None:
        back_to_catalog()
        st.rerun()

    st.button("→ חזרה לקטלוג", on_click=back_to_catalog)
    st.title(space["title"])
    st.write(f"📍 {space['neighborhood']} · {space['store_type']} · 📐 {space['sqm']} מ״ר · 🕒 {space['open_hours']}")
    st.markdown(price_html(space), unsafe_allow_html=True)
    if has_discount(space):
        st.markdown(f'<div class="badge">{html.escape(discount_badge_text(space))}</div>', unsafe_allow_html=True)

    images = get_images(space)
    with st.container(key="details_box"):
        if len(images) > 1:
            for tab, img in zip(st.tabs([f"תמונה {i}" for i in range(1, len(images) + 1)]), images):
                with tab:
                    st.image(img, use_container_width=True)
        else:
            st.image(images[0], use_container_width=True)

    st.divider()
    st.subheader("📝 בקשת שיריון")
    q = compute_quote(space, f["start"], f["end"])
    st.info(f"תאריכים: {f['start']:%d/%m/%Y} - {f['end']:%d/%m/%Y} (ניתן לשנות בתפריט הצד)")
    render_quote(space, q)

    with st.form("booking_form"):
        brand = st.text_input("שם המותג")
        insta = st.text_input("קישור לאינסטגרם", placeholder="https://instagram.com/your_brand")
        phone = st.text_input("מספר טלפון", placeholder="050-0000000")
        st.text_input("סה״כ ימים מבוקשים (לפי התאריכים בתפריט הצד)", value=str(q["days"]), disabled=True)

        with st.expander("תקנון ותנאי ביטול"):
            st.markdown(
                """
                **1. הזמנה:** השיריון מאושר רק לאחר אישור סופי של הנהלת הפלטפורמה ובעל העסק.
                **2. תשלום:** התשלום מתבצע מראש. אי תשלום עד 48 שעות מהאישור יבטל את השיריון.
                **3. ביטול:** עד 7 ימים לפני המועד - החזר מלא. 3-7 ימים - החזר של 50%. פחות מ-72 שעות - ללא החזר.
                **4. אחריות:** המותג אחראי לסחורתו ולניקיון הפינה בסיום האירוע.
                """
            )
        agreed = st.checkbox("קראתי ואישרתי את התקנון")
        submitted = st.form_submit_button("בקש שיריון", type="primary")

    if submitted:
        errors = []
        if not brand.strip():
            errors.append("יש להזין שם מותג")
        if "instagram.com" not in insta.lower() and not insta.strip().startswith("@"):
            errors.append("יש להזין קישור אינסטגרם תקין (או @שם_משתמש)")
        if not re.fullmatch(r"0?5\d{8}", re.sub(r"[-\s]", "", phone)):
            errors.append("יש להזין מספר טלפון נייד ישראלי תקין")
        if q["days"] == 0:
            errors.append("טווח התאריכים אינו תקין")
        if not agreed:
            errors.append("יש לאשר את התקנון כדי להמשיך")

        if errors:
            st.session_state.wa_url = None
            for e in errors:
                st.error(e)
        else:
            st.session_state.wa_url = build_whatsapp_url(space, q, brand.strip(), insta.strip(), phone.strip(), f)

    if st.session_state.wa_url:
        st.success("הבקשה מוכנה! נשאר רק לשלוח אותה בוואטסאפ 👇")
        st.link_button("לחץ כאן לשליחת הבקשה בוואטסאפ", st.session_state.wa_url, type="primary")

# ----------------------------------------------------------------------------
# Main router
# ----------------------------------------------------------------------------
spaces = load_spaces()

with st.sidebar:
    filters = render_filters(spaces)
    render_admin_panel(spaces)

if st.session_state.view == "details":
    render_details(spaces, filters)
else:
    render_catalog(spaces, filters)
