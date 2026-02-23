# pages/admin_page.py
import streamlit as st
import model
import controller


def render_admin():
    st.subheader("🛠️ จัดการผู้ใช้ระบบ (Users)")

    # ---- Add user ----
    st.markdown("### ➕ เพิ่มผู้ใช้")

    with st.form("add_user_form"):
        c1, c2 = st.columns(2)

        with c1:
            username = st.text_input("ชื่อผู้ใช้ (username)")
            role = st.selectbox("role (หน้าที่)", ["staff", "admin"])

        with c2:
            password = st.text_input("รหัสผ่านเริ่มต้น", type="password")
            is_active = st.checkbox("เปิดใช้งาน", value=True)

        submitted = st.form_submit_button("เพิ่มผู้ใช้")

    if submitted:
        ok, msgs = controller.create_user(username, password, role, is_active)
        if not ok:
            for m in msgs:
                st.error("⚠ " + m)
        else:
            for m in msgs:
                st.success(m)
            st.rerun()

    st.divider()

    # ---- List users ----
    st.markdown("### 👥 รายชื่อผู้ใช้")

    users_df = model.get_all_users()
    if users_df.empty:
        st.info("ยังไม่มีผู้ใช้ในระบบ")
        return

    st.dataframe(users_df, use_container_width=True)
    st.divider()

    # ---- Change role/status ----
    st.markdown("### 🔧 เปลี่ยน role / สถานะ")

    # ✅ แก้ตรงนี้: ไม่ใช้ r['สถานะ'] แล้ว
    options = [
    f"{r['id']} - {r['username']} ({r['role']}) [{r['status']}]"
    for _, r in users_df.iterrows()
]


    selected = st.selectbox("เลือกผู้ใช้", options)
    user_id = int(selected.split(" - ")[0])

    new_role = st.selectbox(
        "role ใหม่",
        ["staff", "admin"],
        key="role_change"
    )

    new_active = st.selectbox(
        "สถานะใหม่",
        ["ใช้งาน", "ปิดใช้งาน"],
        key="active_change"
    )

    c1, c2 = st.columns(2)

    with c1:
        if st.button("บันทึก role"):
            current_username = st.session_state.get("user", {}).get("username", "")
            ok, msgs = controller.set_user_role(
                user_id, new_role, current_username
            )
            if not ok:
                for m in msgs:
                    st.error("⚠ " + m)
            else:
                for m in msgs:
                    st.success(m)
                st.rerun()

    with c2:
        if st.button("บันทึกสถานะ"):
            current_username = st.session_state.get("user", {}).get("username", "")
            is_active = (new_active == "ใช้งาน")
            ok, msgs = controller.set_user_active(
                user_id, is_active, current_username
            )
            if not ok:
                for m in msgs:
                    st.error("⚠ " + m)
            else:
                for m in msgs:
                    st.success(m)
                st.rerun()
