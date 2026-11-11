"""
Shop-in-Shop Pop-up Marketplace - MVP
הרצה:  pip install streamlit  &&  streamlit run app.py
"""
import re
from datetime import date, timedelta
from urllib.parse import quote

import streamlit as st

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
st.set_page_config(page_title="פופ-אפ בשטח | שכירות פינות מכירה", page_icon="🛍️", layout="wide")

# TODO: replace with Davir's real WhatsApp number (international format, no "+" or leading 0)
DAVIR_WHATSAPP = "9725XXXXXXXX"

# ----------------------------------------------------------------------------
# RTL CSS
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global RTL */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
    [data-testid="stMarkdownContainer"], .stTextInput, .stDateInput, .stMultiSelect,
    .stCheckbox, .stExpander, label, p, h1, h2, h3, h4, li {
        direction: rtl;
        text-align: right;
    }
    /* Sidebar on the right side */
    [data-testid="stAppViewContainer"] { flex-direction: row-reverse; }
    [data-testid="stSidebar"] { direction: rtl; }
    /* Buttons: keep text centered, RTL flow */
    .stButton > button, .stFormSubmitButton > button, .stLinkButton > a {
        direction: rtl; width: 100%; font-weight: 600;
    }
    /* Inputs typed text right-aligned (phone/links stay LTR-friendly) */
    input, textarea { direction: rtl; text-align: right; }
    /* Sliders behave badly when mirrored - keep the track LTR */
    [data-testid="stSlider"] > div { direction: ltr; }
    [data-testid="stSlider"] label { direction: rtl; text-align: right; }
    /* Tabs and expander headers */
    .stTabs [data-baseweb="tab-list"] { direction: rtl; }
    [data-testid="stExpander"] summary { direction: rtl; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Mock data
# ----------------------------------------------------------------------------
def _imgs(seed: int) -> list[str]:
    """3 placeholder images per space."""
    return [f"https://picsum.photos/seed/popup{seed}-{n}/640/420" for n in range(1, 4)]


SPACES = [
    {"id": 1, "title": "פינה בקפה בוטיק", "neighborhood": "צפון ישן", "price": 450,
     "sqm": 4, "images": _imgs(1), "open_hours": "08:00-16:00", "store_type": "בית קפה"},
    {"id": 2, "title": "מדף תצוגה בחנות בגדים", "neighborhood": "פלורנטין", "price": 700,
     "sqm": 6, "images": _imgs(2), "open_hours": "10:00-20:00", "store_type": "חנות בגדים"},
    {"id": 3, "title": "שולחן מול הכניסה", "neighborhood": "שכונת נווה צדק", "price": 900,
     "sqm": 8, "images": _imgs(3), "open_hours": "09:00-19:00", "store_type": "חנות עיצוב"},
    {"id": 4, "title": "פינת ישיבה בבית קפה שכונתי", "neighborhood": "צפון ישן", "price": 350,
     "sqm": 3, "images": _imgs(4), "open_hours": "07:30-15:00", "store_type": "בית קפה"},
    {"id": 5, "title": "חלון ראווה בחנות וינטג'", "neighborhood": "רמת גן - הבורסה", "price": 1200,
     "sqm": 10, "images": _imgs(5), "open_hours": "10:00-21:00", "store_type": "חנות וינטג'"},
    {"id": 6, "title": "קיר גלריה בקפה-ספרים", "neighborhood": "פלורנטין", "price": 550,
     "sqm": 5, "images": _imgs(6), "open_hours": "09:00-22:00", "store_type": "בית קפה"},
]
SPACES_BY_ID = {s["id"]: s for s in SPACES}

# ----------------------------------------------------------------------------
# Session state - single source of truth for navigation
# ----------------------------------------------------------------------------
st.session_state.setdefault("view", "catalog")       # "catalog" | "details"
st.session_state.setdefault("selected_id", None)
st.session_state.setdefault("wa_url", None)          # generated WhatsApp link


def open_details(space_id: int) -> None:
    """Callback: switch to the details view."""
    st.session_state.view = "details"
    st.session_state.selected_id = space_id
    st.session_state.wa_url = None


def back_to_catalog() -> None:
    """Callback: return to the catalog."""
    st.session_state.view = "catalog"
    st.session_state.selected_id = None
    st.session_state.wa_url = None


# ----------------------------------------------------------------------------
# Sidebar filters
# ----------------------------------------------------------------------------
def next_friday(today: date) -> date:
    return today + timedelta(days=(4 - today.weekday()) % 7)


with st.sidebar:
    st.header("🔎 סינון תוצאות")

    default_start = next_friday(date.today())
    start_date = st.date_input("תאריך התחלה", value=default_start, min_value=date.today())
    end_date = st.date_input("תאריך סיום", value=default_start + timedelta(days=1), min_value=date.today())
    if end_date < start_date:
        st.error("תאריך הסיום חייב להיות אחרי תאריך ההתחלה")

    all_hoods = sorted({s["neighborhood"] for s in SPACES})
    all_types = sorted({s["store_type"] for s in SPACES})
    sel_hoods = st.multiselect("אזור", all_hoods, placeholder="כל האזורים")
    sel_types = st.multiselect("סוג עסק", all_types, placeholder="כל סוגי העסקים")

    max_price = max(s["price"] for s in SPACES)
    budget = st.slider("תקציב מקסימלי (₪)", min_value=0, max_value=max_price + 300,
                       value=max_price + 300, step=50)


def filtered_spaces() -> list[dict]:
    """Empty multiselect = no restriction on that field."""
    return [
        s for s in SPACES
        if (not sel_hoods or s["neighborhood"] in sel_hoods)
        and (not sel_types or s["store_type"] in sel_types)
        and s["price"] <= budget
    ]


# ----------------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------------
def render_catalog() -> None:
    st.title("🛍️ פופ-אפ בשטח")
    st.caption("שכרו פינה בבית קפה או בחנות ל-Pop-up של סוף שבוע")

    results = filtered_spaces()
    st.subheader(f"נמצאו {len(results)} חללים")
    if not results:
        st.info("לא נמצאו חללים התואמים את הסינון. נסו להרחיב את החיפוש.")
        return

    COLS = 3
    for row_start in range(0, len(results), COLS):
        cols = st.columns(COLS)
        for col, space in zip(cols, results[row_start:row_start + COLS]):
            with col, st.container(border=True):
                st.image(space["images"][0], use_container_width=True)
                st.markdown(f"### {space['title']}")
                st.write(f"📍 {space['neighborhood']} · {space['store_type']}")
                st.write(f"📐 {space['sqm']} מ״ר")
                st.write(f"🕒 {space['open_hours']}")
                st.markdown(f"**💰 {space['price']} ₪ לסוף שבוע**")
                st.button("לפרטים והרשמה", key=f"details_{space['id']}",
                          on_click=open_details, args=(space["id"],), type="primary")


def build_whatsapp_url(space: dict, brand: str, insta: str, phone: str) -> str:
    msg = (
        "שלום דביר, אשמח לשריין חלל פופ-אפ 🙌\n"
        f"חלל: {space['title']} ({space['neighborhood']})\n"
        f"תאריכים: {start_date:%d/%m/%Y} - {end_date:%d/%m/%Y}\n"
        f"מותג: {brand}\n"
        f"אינסטגרם: {insta}\n"
        f"טלפון: {phone}"
    )
    return f"https://wa.me/{DAVIR_WHATSAPP}?text={quote(msg)}"


def render_details() -> None:
    space = SPACES_BY_ID.get(st.session_state.selected_id)
    if space is None:  # safety net
        back_to_catalog()
        st.rerun()

    st.button("→ חזרה לקטלוג", on_click=back_to_catalog)
    st.title(space["title"])
    st.write(f"📍 {space['neighborhood']} · {space['store_type']} · 📐 {space['sqm']} מ״ר · "
             f"🕒 {space['open_hours']}")
    st.markdown(f"### 💰 {space['price']} ₪ לסוף שבוע")

    # Image gallery: one tab per image
    tabs = st.tabs([f"תמונה {i}" for i in range(1, len(space["images"]) + 1)])
    for tab, url in zip(tabs, space["images"]):
        with tab:
            st.image(url, use_container_width=True)

    st.divider()
    st.subheader("📝 בקשת שיריון")
    st.info(f"תאריכים נבחרים: {start_date:%d/%m/%Y} - {end_date:%d/%m/%Y} (ניתן לשנות בתפריט הצד)")

    with st.form("booking_form"):
        brand = st.text_input("שם המותג")
        insta = st.text_input("קישור לאינסטגרם", placeholder="https://instagram.com/your_brand")
        phone = st.text_input("מספר טלפון", placeholder="050-0000000")

        with st.expander("תקנון ותנאי ביטול"):
            st.markdown(
                """
                **1. הזמנה:** השיריון מאושר רק לאחר אישור סופי מצד הנהלת הפלטפורמה ובעל העסק.

                **2. תשלום:** התשלום מתבצע מראש. אי תשלום עד 48 שעות מהאישור יבטל את השיריון.

                **3. ביטול:** ביטול עד 7 ימים לפני המועד - החזר מלא. 3-7 ימים - החזר של 50%.
                פחות מ-72 שעות - ללא החזר.

                **4. אחריות:** המותג אחראי לסחורתו ולניקיון הפינה בסיום האירוע.

                *(טקסט לדוגמה בלבד - יש להחליף בתקנון משפטי מאושר)*
                """
            )

        agreed = st.checkbox("קראתי ואישרתי את התקנון")
        submitted = st.form_submit_button("בקש שיריון מול דביר", type="primary")

    if submitted:
        errors = []
        if not brand.strip():
            errors.append("יש להזין שם מותג")
        if "instagram.com" not in insta.lower() and not insta.strip().startswith("@"):
            errors.append("יש להזין קישור אינסטגרם תקין (או @שם_משתמש)")
        if not re.fullmatch(r"0?5\d{8}", re.sub(r"[-\s]", "", phone)):
            errors.append("יש להזין מספר טלפון נייד ישראלי תקין")
        if end_date < start_date:
            errors.append("טווח התאריכים אינו תקין")
        if not agreed:
            errors.append("יש לאשר את התקנון כדי להמשיך")

        if errors:
            st.session_state.wa_url = None
            for e in errors:
                st.error(e)
        else:
            st.session_state.wa_url = build_whatsapp_url(
                space, brand.strip(), insta.strip(), phone.strip())

    # Link button lives outside the form (not allowed inside st.form)
    if st.session_state.wa_url:
        st.success("הבקשה מוכנה! נשאר רק לשלוח אותה בוואטסאפ 👇")
        st.link_button("לחץ כאן לשליחת הבקשה בוואטסאפ", st.session_state.wa_url,
                       type="primary")


# ----------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------
if st.session_state.view == "details":
    render_details()
else:
    render_catalog()
