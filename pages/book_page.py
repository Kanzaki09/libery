# pages/book_page.py
import streamlit as st
import controller
import model

# -----------------
# Helpers
# -----------------
def reset_book_form():
    st.session_state["book_add_title"] = ""
    st.session_state["book_add_author"] = ""

def on_save_book():
    title = st.session_state.get("book_add_title", "").strip()
    author = st.session_state.get("book_add_author", "").strip()

    ok, msgs = controller.create_book(title, author)
    for m in msgs:
        st.success(m) if ok else st.error(m)

    if ok:
        reset_book_form()

# -----------------
# UI
# -----------------
def render_book():
    st.subheader("➕ เพิ่มข้อมูลหนังสือใหม่")

    st.text_input("ชื่อหนังสือ", key="book_add_title")
    st.text_input("ผู้แต่ง", key="book_add_author")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.button("บันทึก", on_click=on_save_book, key="book_add_save")
    with col2:
        st.button("ล้างฟอร์ม", on_click=reset_book_form, key="book_add_reset")

    # -------- Read --------
    st.subheader("📖 รายการหนังสือทั้งหมด")
    books_df = model.fetch_books()

    if books_df.empty:
        st.info("ยังไม่มีข้อมูลหนังสือ")
        return

    st.dataframe(books_df, use_container_width=True)

    # -------- Delete --------
    st.subheader("🗑️ ลบหนังสือ")
    for _, row in books_df.iterrows():
        c1, c2, c3 = st.columns([4, 3, 1])
        with c1:
            st.write(f"📘 **{row['title']}** — {row['author']}")
        with c2:
            st.write(f"รหัส: {row['id']}")
        with c3:
            if st.button("ลบ", key=f"del_book_{row['id']}"):
                controller.remove_book(row["id"])
                st.success("ลบหนังสือแล้ว")
                st.rerun()

    # -------- Update --------
    st.subheader("✏️ แก้ไขหนังสือ")

    book_options = [
        f"{row['id']} - {row['title']}"
        for _, row in books_df.iterrows()
    ]

    selected = st.selectbox(
        "เลือกหนังสือ",
        book_options,
        key="book_edit_select"
    )

    book_id = int(selected.split(" - ")[0])
    row = books_df[books_df["id"] == book_id].iloc[0]

    with st.form("edit_book_form"):
        new_title = st.text_input(
            "ชื่อหนังสือ",
            value=row["title"],
            key="book_edit_title"
        )
        new_author = st.text_input(
            "ผู้แต่ง",
            value=row["author"],
            key="book_edit_author"
        )
        submit = st.form_submit_button("บันทึกการแก้ไข")

    if submit:
        ok, msgs = controller.edit_book(book_id, new_title, new_author)
        for m in msgs:
            st.success(m) if ok else st.error(m)
        if ok:
            st.rerun()
