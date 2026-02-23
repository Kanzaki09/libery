import streamlit as st
from model import (
    insert_book,
    fetch_books,
    delete_book,
    update_book
)

from model import (
    insert_member,
    member_code_exists,
    email_exists,
    delete_member,
    update_member,
    fetch_members
)

def reset_form():
    st.session_state["book_add_title"] = ""
    st.session_state["book_add_author"] = ""

def save_book():
    title = st.session_state.get("book_add_title", "")
    author = st.session_state.get("book_add_author", "")


    if title.strip() == "":
        st.error("❌ กรุณากรอกชื่อหนังสือ")
        return

    insert_book(title.strip(), author.strip())
    st.success(f"✅ บันทึก '{title}' สำเร็จ")
    reset_form()


def get_books():
    return fetch_books()


def remove_book(book_id: int):
    delete_book(book_id)
    st.success("🗑️ ลบหนังสือเรียบร้อยแล้ว")
    st.rerun()


def edit_book(book_id, title, author):
    if title.strip() == "":
        st.error("❌ ชื่อหนังสือห้ามว่าง")
        return

    update_book(book_id, title.strip(), author.strip())
    st.success("✏️ แก้ไขข้อมูลเรียบร้อยแล้ว")
    st.rerun()


def reset_member_form():
    st.session_state["member_code"] = ""
    st.session_state["member_name"] = ""
    st.session_state["gender"] = "ไม่ระบุ"
    st.session_state["member_email"] = ""
    st.session_state["member_phone"] = ""
    st.session_state["is_active"] = True


def add_member_controller(member_code, name, gender, email, phone, is_active):
    errors = []

    if member_code.strip() == "":
        errors.append("❌ กรุณากรอก รหัสสมาชิก")
    if name.strip() == "":
        errors.append("❌ กรุณากรอก ชื่อ-นามสกุล")

    if member_code_exists(member_code):
        errors.append(f"❌ รหัสสมาชิก {member_code} มีอยู่แล้ว")

    if email and email_exists(email):
        errors.append(f"❌ อีเมล {email} ถูกใช้งานแล้ว")

    if errors:
        for err in errors:
            st.error(err)
        return

    insert_member(
        member_code.strip(),
        name.strip(),
        gender,
        email.strip(),
        phone.strip(),
        is_active
    )

    st.success("✅ สมัครสมาชิกสำเร็จ")
    reset_member_form()


def get_members():
    return fetch_members()


def remove_member_controller(member_id):
    delete_member(member_id)
    st.success("🗑️ ลบสมาชิกเรียบร้อยแล้ว")
    st.rerun()


def update_member_controller(
    member_id,
    member_code,
    name,
    gender,
    email,
    phone,
    is_active
):
    if member_code.strip() == "":
        st.error("❌ รหัสสมาชิกห้ามว่าง")
        return

    update_member(
        member_id,
        member_code.strip(),
        name.strip(),
        gender,
        email.strip(),
        phone.strip(),
        is_active
    )

    st.success("✏️ แก้ไขข้อมูลสมาชิกเรียบร้อยแล้ว")
    st.rerun()

#################################################
# user login
#################################################
# --- เพิ่มท้ายไฟล์ controller.py ---

import hashlib
import model

def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def login(username: str, password: str):
    """
    Controller-level login
    return: (ok: bool, messages: list[str], user_info: dict | None)
    user_info: {"id": .., "username": .., "role": ..}
    """
    errors = []

    if not username.strip():
        errors.append("กรุณากรอก **ชื่อผู้ใช้**")
    if not password.strip():
        errors.append("กรุณากรอก **รหัสผ่าน**")

    if errors:
        return False, errors, None

    u = model.get_user_auth_row(username)

    if not u:
        return False, ["⚠ ไม่พบบัญชีผู้ใช้นี้ในระบบ"], None

    if _hash_password(password) != u["password_hash"]:
        return False, ["⚠ รหัสผ่านไม่ถูกต้อง"], None

    user_info = {
        "id": u["id"],
        "username": u["username"],
        "role": u["role"]
    }

    return True, ["✅ เข้าสู่ระบบสำเร็จ"], user_info

##############################################
# manage user
##############################################
import hashlib
import model

def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def login(username: str, password: str):
    """Login (มีการเช็ค active)"""
    errors = []

    if not username.strip():
        errors.append("กรุณากรอก **ชื่อผู้ใช้**")
    if not password.strip():
        errors.append("กรุณากรอก **รหัสผ่าน**")

    if errors:
        return False, errors, None

    u = model.get_user_auth_row(username)

    if not u:
        return False, ["⚠ ไม่พบบัญชีผู้ใช้นี้ในระบบ"], None

    if u["is_active"] != 1:
        return False, ["⚠ บัญชีนี้ถูกปิดใช้งาน กรุณาติดต่อผู้ดูแลระบบ"], None

    if _hash_password(password) != u["password_hash"]:
        return False, ["⚠ รหัสผ่านไม่ถูกต้อง"], None

    user_info = {
        "id": u["id"],
        "username": u["username"],
        "role": u["role"]
    }

    return True, ["✅ เข้าสู่ระบบสำเร็จ"], user_info


# -------- Admin actions --------
def create_user(username: str, password: str, role: str, is_active: bool = True):
    errors = []

    username = username.strip()
    password = password.strip()

    if not username:
        errors.append("กรุณากรอก **ชื่อผู้ใช้**")
    if len(username) < 3:
        errors.append("ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร")

    if not password:
        errors.append("กรุณากรอก **รหัสผ่าน**")
    if len(password) < 4:
        errors.append("รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร")

    if role not in ("admin", "staff"):
        errors.append("role ต้องเป็น admin หรือ staff")

    if username and model.is_username_exists(username):
        errors.append(f"ชื่อผู้ใช้ **{username}** มีอยู่แล้ว")

    if errors:
        return False, errors

    model.add_user(
        username=username,
        password_hash=_hash_password(password),
        role=role,
        is_active=1 if is_active else 0
    )

    return True, [f"✅ เพิ่มผู้ใช้ '{username}' เรียบร้อยแล้ว"]


def set_user_role(user_id: int, new_role: str, current_username: str):
    """เปลี่ยน role (กันลดสิทธิ์ตัวเอง)"""
    if new_role not in ("admin", "staff"):
        return False, ["role ต้องเป็น admin หรือ staff"]

    users_df = model.get_all_users()
    me = users_df[users_df["username"] == current_username]

    if (
        not me.empty
        and int(me.iloc[0]["id"]) == int(user_id)
        and new_role != "admin"
    ):
        return False, ["ไม่อนุญาตให้ลดสิทธิ์ของผู้ดูแลระบบที่กำลังล็อกอินอยู่"]

    model.update_user_role(int(user_id), new_role)
    return True, ["✅ เปลี่ยน role เรียบร้อยแล้ว"]


def set_user_active(user_id: int, is_active: bool, current_username: str):
    """เปิด/ปิด user (กันปิดตัวเอง)"""
    users_df = model.get_all_users()
    me = users_df[users_df["username"] == current_username]

    if (
        not me.empty
        and int(me.iloc[0]["id"]) == int(user_id)
        and not is_active
    ):
        return False, ["ไม่อนุญาตให้ปิดใช้งานบัญชีที่กำลังล็อกอินอยู่"]

    model.update_user_active(int(user_id), 1 if is_active else 0)
    return True, ["✅ เปลี่ยนสถานะผู้ใช้เรียบร้อยแล้ว"]

# ============================================================
# Borrow: multi-book per transaction
# ============================================================
def borrow_books(member_id: int, staff_user_id: int, due_date_iso: str | None, book_ids: list[int], note: str | None = None):
    """
    สร้างรายการยืม 1 ครั้ง (หลายเล่ม)
    - ต้องระบุ staff_user_id เพื่อบันทึกว่าใครเป็นผู้ทำรายการ
    """
    errors = []
    if not member_id:
        errors.append("กรุณาเลือกสมาชิก")
    if not staff_user_id:
        errors.append("ไม่พบข้อมูลผู้ทำรายการ (กรุณาเข้าสู่ระบบใหม่)")
    if not book_ids:
        errors.append("กรุณาเลือกหนังสืออย่างน้อย 1 เล่ม")
    if errors:
        return False, errors, None


    try:
        tx_id = model.create_borrow_transaction(
            member_id=int(member_id),
            staff_user_id=int(staff_user_id),
            default_due_date=due_date_iso,
            book_ids=[int(x) for x in book_ids],
            note=note
        )
        return True, [f"บันทึกการยืมเรียบร้อยแล้ว (TX: {tx_id})"], tx_id
    except Exception as e:
        return False, [f"ไม่สามารถบันทึกการยืมได้: {e}"], None


def return_book_item(item_id: int, return_staff_user_id: int):
    """คืนหนังสือทีละเล่ม พร้อมบันทึกผู้ทำรายการคืน"""
    if not item_id:
        return False, ["กรุณาเลือกรายการที่จะคืน"]
    if not return_staff_user_id:
        return False, ["ไม่พบข้อมูลผู้ทำรายการ (กรุณาเข้าสู่ระบบใหม่)"]


    ok = model.return_borrow_item(int(item_id), int(return_staff_user_id))
    if not ok:
        return False, ["ไม่พบรายการที่ยังไม่คืน หรือรายการถูกคืนแล้ว"]
    return True, ["บันทึกการคืนเรียบร้อยแล้ว"]


def return_book_items(item_ids: list[int], return_staff_user_id: int):
    """
    คืนหนังสือหลายรายการ (ติ๊กได้หลายเล่ม) พร้อมบันทึกผู้ทำรายการคืน
    return: (ok:bool, messages:list[str])
    """
    if not item_ids:
        return False, ["กรุณาเลือกรายการที่จะคืนอย่างน้อย 1 รายการ"]
    if not return_staff_user_id:
        return False, ["ไม่พบข้อมูลผู้ทำรายการ (กรุณาเข้าสู่ระบบใหม่)"]


    success = 0
    failed = []


    for item_id in item_ids:
        try:
            ok = model.return_borrow_item(int(item_id), int(return_staff_user_id))
            if ok:
                success += 1
            else:
                failed.append(int(item_id))
        except Exception:
            failed.append(int(item_id))


    msgs = [f"บันทึกการคืนสำเร็จ {success} รายการ"]
    if failed:
        msgs.append(f"รายการที่คืนไม่สำเร็จ/ถูกคืนแล้ว: {failed}")


    return True, msgs


