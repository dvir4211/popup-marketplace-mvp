"""
Shop-in-Shop Pop-up Marketplace - MVP (v2)
Run:  pip install "streamlit>=1.39"  &&  streamlit run app.py

Architecture
------------
* spaces.json  -> persistent storage. Stores ONLY `host_price` (what the store owner wants).
* display_price = host_price * 1.12 (platform fee), calculated on the fly everywhere in the UI.
* st.session_state drives routing between the "catalog" and "details" views.
"""
import hmac
import html
import json
import re
import uuid
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

import streamlit as st

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
st.set_page_config(page_title="פופ-אפ בשטח", page_icon="🛍️", layout="wide")

DATA_FILE = Path("spaces.json")
PLATFORM_FEE = 0.12                      # 12% platform fee added on top of host price
ADMIN_PASSWORD = "dvir2026"              # TODO: move to st.secrets in production
DAVIR_WHATSAPP = "9725XXXXXXXX"          # TODO: real number, international format, no "+"
HERO_IMAGE = "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=1800&q=80"
FALLBACK_IMAGE = "https://images.unsplash.com/photo-1445116572660-236099ec97a0?auto=format&fit=crop&w=900&q=80"

# ----------------------------------------------------------------------------
# Styling: strict RTL + warm high-end look
# ----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;800&display=swap');

:root {
    --crimson: #B3202E;
    --crimson-dark: #8E1823;
    --bg: #FBF8F4;
    --card: #FFFFFF;
    --text: #2F2F33;
    --muted: #7A7A80;
}

/* Hide default Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stHeader"] {background: transparent;}

/* Strict RTL */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
[data-testid="stMarkdownContainer"], label, p, h1, h2, h3, h4, li, input, textarea {
    direction: rtl;
    text-align: right;
    font-family: 'Heebo', sans-serif !important;
    color: var(--text);
}
.stApp { background: var(--bg); }
[data-testid="stAppViewContainer"] { flex-direction: row-reverse; }   /* sidebar on the right */
[data-testid="stSidebar"] { background: #FFFFFF; box-shadow: -4px 0 24px rgba(0,0,0,.05); }
[data-testid="stSlider"] > div { direction: ltr; }                    /* slider track stays LTR */
[data-testid="stSlider"] label { direction: rtl; text-align: right; }
.stTabs [data-baseweb="tab-list"], [data-testid="stExpander"] summary { direction: rtl; }

/* Primary buttons (button, form submit, link button) */
button[kind^="primary"], [data-testid^="stBaseButton-primary"],
[data-testid="stBaseLinkButton-primary"], a[kind="primary"] {
    background: var(--crimson) !important; border: none !important; color: #fff !important;
    border-radius: 12px !important; font-weight: 700 !important; width: 100%;
    box-shadow: 0 6px 16px rgba(179,32,46,.25); transition: all .2s ease;
}
button[kind^="primary"]:hover, [data-testid^="stBaseButton-primary"]:hover,
[data-testid="stBaseLinkButton-primary"]:hover {
    background: var(--crimson-dark) !important; transform: translateY(-1px);
}
[data-testid="stBaseButton-secondary"] { border-radius: 12px; width: 100%; }
[data-testid="stBaseLinkButton-primary"] p { color: #fff !important; text-align: center; }

/* Cards (containers created with key="card_<id>") */
[class*="st-key-card_"] {
    background: var(--card); border-radius: 18px; padding: 14px;
    box-shadow: 0 8px 28px rgba(60,40,30,.08); border: 1px solid #F1EBE4;
    transition: transform .2s ease, box-shadow .2s ease;
}
[class*="st-key-card_"]:hover { transform: translateY(-3px); box-shadow: 0 14px 34px rgba(60,40,30,.14); }
[class*="st-key-card_"] img { height: 210px; object-fit: cover; border-radius: 12px; }
.st-key-details_box img { max-height: 460px; object-fit: cover; border-radius: 18px; box-shadow: 0 10px 30px rgba(0,0,0,.12); }
[data-testid="stForm"] { background: #fff; border-radius: 18px; border: 1px solid #F1EBE4; box-shadow: 0 8px 28px rgba(60,40,30,.06); }

.card-title { font-size: 1.25rem; font-weight: 800; margin: 8px 0 4px; }
.card-meta { color: var(--muted); font-size: .95rem; margin-bottom: 2px; }
.price { color: var(--crimson); font-size: 1.5rem; font-weight: 800; margin: 8px 0 10px; }
.price span { color: var(--muted); font-size: .85rem; font-weight: 400; }

/* Hero */
.hero {
    height: 340px; border-radius: 22px; margin-bottom: 14px; position: relative;
    background: linear-gradient(to top, rgba(30,15,15,.65), rgba(30,15,15,.05)), url('__HERO__') center/cover;
    box-shadow: 0 14px 40px rgba(60,40,30,.2); display: flex; align-items: flex-end;
}
.hero-text { padding: 28px 34px; color: #fff; }
.hero-text h1 { color: #fff !important; font-size: 2.6rem; font-weight: 800; margin: 0; }
.hero-text p { color: #f3e9e2 !important; font-size: 1.15rem; margin: 4px 0 0; }

/* CSS-only marquee */
.marquee {
    direction: ltr; overflow: hidden; white-space: nowrap; background: #fff; border-radius: 14px;
    padding: 12px 0; margin-bottom: 26px; border: 1px solid #F1EBE4; box-shadow: 0 4px 14px rgba(0,0,0,.05);
}
.marquee span {
    display: inline-block; padding-left: 100%; font-weight: 700; color: var(--crimson);
    animation: marquee 16s linear infinite;
}
@keyframes marquee { 0% {transform: translateX(0);} 100% {transform: translateX(-100%);} }

/* Empty state */
.empty-state {
    text-align: center; background: #fff; border-radius: 22px; padding: 60px 24px;
    box-shadow: 0 10px 34px rgba(60,40,30,.08); border: 1px dashed #E6D6CC;
}
.empty-state .icon { font-size: 3.4rem; }
.empty-state h2 { color: var(--crimson); text-align: center; margin: 10px 0 6px; font-weight: 800; }
.empty-state p { color: var(--muted); text-align: center; font-size: 1.1rem; }
</style>
""".replace("__HERO__", HERO_IMAGE)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Data layer (spaces.json)
# ----------------------------------------------------------------------------
def load_spaces() -> list[dict]:
    """Read spaces.json; create it with [] if missing or unreadable."""
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")
        return []
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_spaces(spaces: list[dict]) -> None:
    DATA_FILE.write_text(json.dumps(spaces, ensure_ascii=False, indent=2), encoding="utf-8")


def display_price(space: dict) -> int:
    """host_price + 12% platform fee, rounded half-up to the nearest integer."""
    return int(space["host_price"] * (1 + PLATFORM_FEE) + 0.5)


# ----------------------------------------------------------------------------
# Session state / routing
# ----------------------------------------------------------------------------
st.session_state.setdefault("view", "catalog")      # "catalog" | "details"
st.session_state.setdefault("selected_id", None)
st.session_state.setdefault("wa_url", None)


def open_details(space_id: str) -> None:
    st.session_state.update(view="details", selected_id=space_id, wa_url=None)


def back_to_catalog() -> None:
    st.session_state.update(view="catalog", selected_id=None, wa_url=None)


# ----------------------------------------------------------------------------
# Sidebar: filters + hidden admin panel
# ----------------------------------------------------------------------------
def next_friday(today: date) -> date:
    return today + timedelta(days=(4 - today.weekday()) % 7)


def render_filters(spaces: list[dict]) -> dict:
    """Yad2-style filters. Returns defaults (and renders nothing) when there are no spaces."""
    start_default = next_friday(date.today())
    f = {"start": start_default, "end": start_default + timedelta(days=1),
         "hoods": [], "types": [], "budget": 10**9}
    if not spaces:
        return f

    st.header("🔎 סינון תוצאות")
    f["start"] = st.date_input("תאריך התחלה", value=start_default, min_value=date.today())
    f["end"] = st.date_input("תאריך סיום", value=start_default + timedelta(days=1), min_value=date.today())
    if f["end"] < f["start"]:
        st.error("תאריך הסיום חייב להיות אחרי תאריך ההתחלה")

    f["hoods"] = st.multiselect("אזור", sorted({s["neighborhood"] for s in spaces}), placeholder="כל האזורים")
    f["types"] = st.multiselect("סוג עסק", sorted({s["store_type"] for s in spaces}), placeholder="כל סוגי העסקים")

    top = max(display_price(s) for s in spaces)
    top = max(50, -(-top // 50) * 50)  # round up to a multiple of 50
    f["budget"] = st.slider("תקציב מקסימלי (₪)", 0, top, top, step=50)  # compared to display_price
    return f


def render_admin_panel(spaces: list[dict]) -> None:
    """Password-protected add/delete panel."""
    with st.expander("ניהול מערכת (Admin)"):
        if msg := st.session_state.pop("flash", None):
            st.success(msg)

        pwd = st.text_input("סיסמה", type="password", key="admin_pwd")
        if not pwd:
            return
        if not hmac.compare_digest(pwd.encode(), ADMIN_PASSWORD.encode()):
            st.error("סיסמה שגויה")
            return

        # ---- Add space ----
        st.markdown("**➕ הוספת חלל חדש**")
        with st.form("admin_add_form", clear_on_submit=True):
            title = st.text_input("שם החלל")
            hood = st.text_input("אזור / שכונה")
            store_type = st.text_input("סוג עסק")
            sqm = st.number_input("שטח (מ״ר)", min_value=1, value=4, step=1)
            hours = st.text_input("שעות פעילות", placeholder="08:00-16:00")
            host_price = st.number_input("מחיר מארח (₪)", min_value=0, value=500, step=10)
            image_url = st.text_input("קישור לתמונה", placeholder="https://...")
            if st.form_submit_button("הוסף חלל", type="primary"):
                if not (title.strip() and hood.strip() and store_type.strip()):
                    st.error("יש למלא שם, אזור וסוג עסק")
                else:
                    spaces.append({
                        "id": uuid.uuid4().hex[:8], "title": title.strip(),
                        "neighborhood": hood.strip(), "store_type": store_type.strip(),
                        "sqm": int(sqm), "open_hours": hours.strip() or "-",
                        "host_price": int(host_price),
                        "image_url": image_url.strip() if image_url.strip().startswith("http") else FALLBACK_IMAGE,
                    })
                    save_spaces(spaces)
                    st.session_state.flash = "החלל נוסף בהצלחה ✅"
                    st.rerun()

        # ---- Delete space ----
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
            <p>אנחנו מקפידים לבחור בקפידה את החללים הטובים ביותר עבורכם.<br>
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

    cols_per_row = 3
    for i in range(0, len(results), cols_per_row):
        for col, s in zip(st.columns(cols_per_row), results[i:i + cols_per_row]):
            with col, st.container(key=f"card_{s['id']}"):
                st.image(s.get("image_url") or FALLBACK_IMAGE, use_container_width=True)
                st.markdown(
                    f"""<div class="card-title">{html.escape(s['title'])}</div>
                    <div class="card-meta">📍 {html.escape(s['neighborhood'])} · {html.escape(s['store_type'])}</div>
                    <div class="card-meta">📐 {s['sqm']} מ״ר · 🕒 {html.escape(s['open_hours'])}</div>
                    <div class="price">₪{display_price(s):,} <span>לסוף שבוע</span></div>""",
                    unsafe_allow_html=True,
                )
                st.button("לפרטים והרשמה", key=f"btn_{s['id']}", type="primary",
                          on_click=open_details, args=(s["id"],))


def build_whatsapp_url(space: dict, brand: str, insta: str, phone: str, f: dict) -> str:
    msg = (
        "שלום דביר, אשמח לשריין חלל פופ-אפ 🙌\n"
        f"חלל: {space['title']} ({space['neighborhood']})\n"
        f"תאריכים: {f['start']:%d/%m/%Y} - {f['end']:%d/%m/%Y}\n"
        f"מחיר: ₪{display_price(space):,}\n"
        f"מותג: {brand}\nאינסטגרם: {insta}\nטלפון: {phone}"
    )
    return f"https://wa.me/{DAVIR_WHATSAPP}?text={quote(msg)}"


def render_details(spaces: list[dict], f: dict) -> None:
    space = next((s for s in spaces if s["id"] == st.session_state.selected_id), None)
    if space is None:  # e.g. deleted by admin while being viewed
        back_to_catalog()
        st.rerun()

    st.button("→ חזרה לקטלוג", on_click=back_to_catalog)
    st.title(space["title"])
    st.write(f"📍 {space['neighborhood']} · {space['store_type']} · 📐 {space['sqm']} מ״ר · 🕒 {space['open_hours']}")
    st.markdown(f'<div class="price">₪{display_price(space):,} <span>לסוף שבוע</span></div>', unsafe_allow_html=True)

    with st.container(key="details_box"):
        st.image(space.get("image_url") or FALLBACK_IMAGE, use_container_width=True)

    st.divider()
    st.subheader("📝 בקשת שיריון")
    st.info(f"תאריכים: {f['start']:%d/%m/%Y} - {f['end']:%d/%m/%Y} (ניתן לשנות בתפריט הצד)")

    with st.form("booking_form"):
        brand = st.text_input("שם המותג")
        insta = st.text_input("קישור לאינסטגרם", placeholder="https://instagram.com/your_brand")
        phone = st.text_input("מספר טלפון", placeholder="050-0000000")

        with st.expander("תקנון ותנאי ביטול"):
            st.markdown(
                """
                **1. הזמנה:** השיריון מאושר רק לאחר אישור סופי של הנהלת הפלטפורמה ובעל העסק.

                **2. תשלום:** התשלום מתבצע מראש. אי תשלום עד 48 שעות מהאישור יבטל את השיריון.

                **3. ביטול:** עד 7 ימים לפני המועד - החזר מלא. 3-7 ימים - החזר של 50%. פחות מ-72 שעות - ללא החזר.

                **4. אחריות:** המותג אחראי לסחורתו ולניקיון הפינה בסיום האירוע.

                *(טקסט לדוגמה בלבד - יש להחליף בתקנון משפטי מאושר)*
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
        if f["end"] < f["start"]:
            errors.append("טווח התאריכים אינו תקין")
        if not agreed:
            errors.append("יש לאשר את התקנון כדי להמשיך")

        if errors:
            st.session_state.wa_url = None
            for e in errors:
                st.error(e)
        else:
            st.session_state.wa_url = build_whatsapp_url(space, brand.strip(), insta.strip(), phone.strip(), f)

    # link_button can't live inside st.form, so it's rendered right after it
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
