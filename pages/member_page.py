# pages/member_page.py
import streamlit as st
import re
import controller
import model

def render_member():
    st.subheader("👤 สมัครสมาชิก")

    # ===== Add member form =====
    with st.form("member_add_form"):
        col1, col2 = st.columns(2)

        with col1:
            member_code = st.text_input(
                "รหัสสมาชิก",
                key="member_add_code"
            )
            name = st.text_input(
                "ชื่อ-นามสกุล",
                key="member_add_name"
            )
            gender = st.selectbox(
                "เพศ",
                ["ไม่ระบุ", "หญิง", "ชาย", "อื่นๆ"],
                key="member_add_gender"
            )

        with col2:
            email = st.text_input(
                "อีเมล",
                key="member_add_email"
            )
            phone = st.text_input(
                "เบอร์โทรศัพท์",
                key="member_add_phone"
            )
            is_active = st.checkbox(
                "ยังใช้งานอยู่",
                True,
                key="member_add_active"
            )

        submitted = st.form_submit_button("บันทึก")

    if submitted:
        errors = []

        if not member_code.strip():
            errors.append("กรุณากรอกรหัสสมาชิก")
        if not name.strip():
            errors.append("กรุณากรอกชื่อ")

        if email.strip():
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                errors.append("รูปแบบอีเมลไม่ถูกต้อง")

        if model.member_code_exists(member_code):
            errors.append("รหัสสมาชิกซ้ำ")

        if email and model.email_exists(email):
            errors.append("อีเมลถูกใช้แล้ว")

        if errors:
            for e in errors:
                st.error(e)
        else:
            controller.add_member(
                member_code,
                name,
                gender,
                email,
                phone,
                is_active
            )
            st.success("สมัครสมาชิกสำเร็จ")
            st.rerun()

    # ===== Read members =====
    st.subheader("📋 รายชื่อสมาชิก")
    df = model.get_all_members()

    if df.empty:
        st.info("ยังไม่มีสมาชิก")
        return

    for _, row in df.iterrows():
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            st.write(f"{row['member_code']} - {row['name']}")
        with c2:
            st.write(row["email"] or "-")
        with c3:
            st.write("ใช้งาน" if row["is_active"] else "ไม่ใช้งาน")
        with c4:
            if st.button(
                "ลบ",
                key=f"del_member_{row['id']}"
            ):
                controller.remove_member(row["id"])
                st.success("ลบสมาชิกแล้ว")
                st.rerun()
