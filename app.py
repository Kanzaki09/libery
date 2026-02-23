import streamlit as st
import model   # ✅ ใช้ model.py ของโปรเจกต์เรา
st.write("MODEL FILE:", model.__file__)
from pages import book_page, member_page, borrow_page, login_page, admin_page, report_page

# =========================
# Page config (ต้องอยู่บนสุด)
# =========================
st.set_page_config(
    page_title="ระบบยืม-คืนหนังสือ",
    page_icon="📚",
    layout="wide"
)

# =========================
# Init session (login)
# =========================
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

if "user" not in st.session_state:
    st.session_state["user"] = None

if "page" not in st.session_state:
    st.session_state["page"] = "books"

# =========================
# Hide Streamlit multipage sidebar
# =========================
st.markdown(
    """
    <style>
    section[data-testid="stSidebarNav"] {display: none !important;}
    div[data-testid="stSidebarNav"] {display: none !important;}
    nav[data-testid="stSidebarNav"] {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# Login Gate
# =========================
if not st.session_state["is_logged_in"]:
    login_page.render_login()
    st.stop()

# =========================
# ✅ INIT DATABASE (เรียกครั้งเดียว)
# =========================
if "db_initialized" not in st.session_state:
    model.ensure_borrow_schema()
    st.session_state["db_initialized"] = True

# =========================
# Header
# =========================
st.title("📚 ระบบยืม-คืนหนังสือ")
st.write("Web App ตัวอย่าง (Streamlit + SQLite, โครงสร้าง MVC)")

# =========================
# Sidebar : User info + Logout
# =========================
user = st.session_state.get("user") or {}

st.sidebar.markdown(f"👤 ผู้ใช้: **{user.get('username', '-')}**")
st.sidebar.markdown(f"🔑 บทบาท: **{user.get('role', '-')}**")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state["is_logged_in"] = False
    st.session_state["user"] = None
    st.session_state["page"] = "books"
    st.rerun()

# =========================
# Sidebar Menu
# =========================
st.sidebar.markdown(
    """
    <style>
    .menu-title {
        text-align: center;
        font-size: 22px;
        font-weight: 700;
        margin: 10px 0 20px 0;
    }
    </style>
    <div class="menu-title">เมนู</div>
    """,
    unsafe_allow_html=True
)

def nav_button(label, key, icon=""):
    if st.sidebar.button(f"{icon} {label}", use_container_width=True):
        st.session_state["page"] = key
        st.rerun()

# เมนูหลัก (admin / staff เหมือนกัน)
nav_button("หนังสือ", "books", "📘")
nav_button("สมาชิก", "members", "👥")
nav_button("ยืม-คืน", "borrows", "🔁")

# เมนูเฉพาะ admin
if user.get("role") == "admin":
    nav_button("จัดการผู้ใช้", "admin", "⚙️")
    nav_button("รายงาน", "reports", "📊")
# =========================
# Routing
# =========================
page = st.session_state.get("page", "books")
role = user.get("role")

if page == "books":
    book_page.render_book()

elif page == "members":
    member_page.render_member()

elif page == "borrows":
    borrow_page.render_borrow()

elif page == "reports":
    if role != "admin":
        st.warning("⚠ หน้านี้อนุญาตเฉพาะผู้ดูแลระบบ (admin) เท่านั้น")
        st.stop()
    report_page.render_report()

elif page == "admin":
    if role != "admin":
        st.warning("⚠ หน้านี้อนุญาตเฉพาะผู้ดูแลระบบ (admin) เท่านั้น")
        st.stop()
    admin_page.render_admin()

else:
    book_page.render_book()
