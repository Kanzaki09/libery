# pages/borrow_page.py
import streamlit as st
from datetime import date, timedelta


import model
import controller


def _contains_ignore_case(series, keyword: str):
    kw = (keyword or "").strip().lower()
    if not kw:
        return series.notna()
    return series.fillna("").astype(str).str.lower().str.contains(kw)


def render_borrow():
    st.subheader("🔄 การทำรายการยืม-คืนหนังสือ")


    # สร้าง schema ยืม-คืน หากยังไม่มี
    model.ensure_borrow_schema()


    # ผู้ทำรายการ (admin/staff)
    user = st.session_state.get("user") or {}
    staff_user_id = user.get("id")


    # =========================
    # ส่วนที่ 1: ทำรายการยืม
    # =========================
    st.markdown("### 1) ทำรายการยืม (ยืมได้มากกว่าหนึ่งเล่มต่อครั้ง)")


    members_df = model.get_active_members()
    if members_df.empty:
        st.warning("ไม่พบสมาชิกที่ใช้งานอยู่ กรุณาเพิ่มสมาชิกก่อนทำรายการยืม")
        return


    # --- 1.1 ค้นหา/เลือกสมาชิก ---
    st.markdown("**1.1 เลือกสมาชิก (ค้นหาจากรหัสสมาชิกหรือชื่อสมาชิก)**")
    member_kw = st.text_input(
        "ค้นหาสมาชิก",
        placeholder="พิมพ์รหัสสมาชิก หรือ ชื่อสมาชิก เช่น M010 หรือ Martha",
        key="borrow_member_kw",
    )


    mdf = members_df.copy()
    mask_m = _contains_ignore_case(mdf["member_code"], member_kw) | _contains_ignore_case(mdf["name"], member_kw)
    mdf = mdf[mask_m].copy()


    if mdf.empty:
        st.info("ไม่พบสมาชิกตามคำค้น กรุณาลองใหม่")
        selected_member_id = None
    else:
        member_options = {
            f"{r['member_code']} : {r['name']}": int(r["id"])
            for _, r in mdf.iterrows()
        }
        member_label = st.selectbox("รายการสมาชิกที่พบ", list(member_options.keys()), key="borrow_member_select")
        selected_member_id = member_options.get(member_label)


    st.markdown("---")


    # --- 1.2 ค้นหา/เพิ่มหนังสือทีละรายการ (ตะกร้ายืม) ---
    st.markdown("**1.2 เพิ่มรายการหนังสือ (ค้นหาจากรหัสหนังสือหรือชื่อหนังสือ และเพิ่มทีละรายการ)**")


    if "borrow_cart" not in st.session_state:
        st.session_state["borrow_cart"] = []  # เก็บ book_id ที่เลือกแล้ว (list[int])


    books_df = model.get_available_books()


    if books_df.empty:
        st.info("ขณะนี้ไม่มีหนังสือสถานะ available สำหรับให้ยืม")
    else:
        book_kw = st.text_input(
            "ค้นหาหนังสือ",
            placeholder="พิมพ์รหัสหนังสือ หรือ ชื่อหนังสือ เช่น 6, 16, หรือ โด, python",
            key="borrow_book_kw",
        )


        bdf = books_df.copy()


        # -----------------------------
        # ✅ ค้นหาแบบ "บางส่วนของรหัส" หรือ "บางส่วนของชื่อ"
        # - id: แปลงเป็น string แล้วค้นแบบ contains (รองรับบางส่วน เช่น '6' เจอ 6,16,60)
        # - title: ค้นแบบ contains โดยไม่สนใจตัวพิมพ์เล็ก-ใหญ่ (case-insensitive)
        # - หากผู้ใช้ไม่พิมพ์อะไร ให้แสดงทั้งหมด
        # -----------------------------
        kw = (book_kw or "").strip()
        if kw:
            mask_id = bdf["id"].astype(str).str.contains(kw, na=False)  # substring ของรหัส
            mask_title = bdf["title"].astype(str).str.contains(kw, case=False, na=False)  # substring ของชื่อ
            mask_b = mask_id | mask_title
            bdf = bdf[mask_b].copy()
        # else: ไม่ต้องกรอง แสดงทั้งหมด


        if bdf.empty:
            st.info("ไม่พบหนังสือตามคำค้น กรุณาลองใหม่")
        else:
            book_options = {
                f"{int(r['id'])} : {r['title']}": int(r["id"])
                for _, r in bdf.iterrows()
            }
            book_label = st.selectbox("รายการหนังสือที่พบ", list(book_options.keys()), key="borrow_book_select")
            add_book_id = book_options.get(book_label)


            col_add1, col_add2 = st.columns([1, 2])
            with col_add1:
                if st.button("➕ เพิ่มรายการ", use_container_width=True):
                    if add_book_id in st.session_state["borrow_cart"]:
                        st.warning("หนังสือเล่มนี้ถูกเพิ่มในรายการแล้ว")
                    else:
                        st.session_state["borrow_cart"].append(int(add_book_id))
                        st.success("เพิ่มรายการเรียบร้อยแล้ว")
                        st.rerun()
            with col_add2:
                if st.button("🧹 ล้างรายการที่เลือกทั้งหมด", use_container_width=True):
                    st.session_state["borrow_cart"] = []
                    st.rerun()
    


    # แสดงตะกร้ายืม
    if st.session_state["borrow_cart"]:
        cart_ids = st.session_state["borrow_cart"]
        cart_df = books_df[books_df["id"].isin(cart_ids)].copy()
        cart_df = cart_df.sort_values("id")


        st.markdown("**รายการหนังสือที่เลือก (ตะกร้ายืม)**")
        st.dataframe(cart_df[["id", "title", "author"]], use_container_width=True)


        # ปุ่มลบรายเล่ม
        st.markdown("**ลบรายการทีละเล่ม**")
        for _, r in cart_df.iterrows():
            bid = int(r["id"])
            c1, c2 = st.columns([6, 1])
            with c1:
                st.write(f"📘 {bid} : {r['title']}")
            with c2:
                if st.button("ลบ", key=f"remove_cart_{bid}"):
                    st.session_state["borrow_cart"] = [x for x in st.session_state["borrow_cart"] if int(x) != bid]
                    st.rerun()
    else:
        st.info("ยังไม่มีรายการหนังสือในตะกร้ายืม")


    # --- 1.3 กำหนดส่ง + บันทึก ---
    default_due = date.today() + timedelta(days=7)
    due_date = st.date_input("กำหนดส่ง (ค่าเริ่มต้นของรายการ)", value=default_due, key="borrow_due")
    note = st.text_input("หมายเหตุ (ถ้ามี)", placeholder="ตัวอย่าง: ยืมเพื่อทำรายงาน/ยืมระยะสั้น ฯลฯ", key="borrow_note")


    can_submit = bool(selected_member_id) and bool(st.session_state["borrow_cart"])
    if st.button("✅ บันทึกการยืม", disabled=not can_submit, use_container_width=True):
        ok, msgs, _tx_id = controller.borrow_books(
            member_id=selected_member_id,
            staff_user_id=staff_user_id,
            due_date_iso=due_date.isoformat() if due_date else None,
            book_ids=[int(x) for x in st.session_state["borrow_cart"]],
            note=note.strip() if note else None
        )
        if not ok:
            for m in msgs:
                st.error("⚠ " + m)
        else:
            for m in msgs:
                st.success("✅ " + m)
            # เคลียร์ตะกร้า
            st.session_state["borrow_cart"] = []
            st.rerun()


    st.divider()


    # =========================
    # ส่วนที่ 2: ทำรายการคืน
    # =========================
    st.markdown("### 2) ทำรายการคืน (ค้นหาสมาชิก → ดูรายการค้างส่ง → ติ๊กคืนได้หลายเล่ม)")


    st.markdown("**2.1 เลือกสมาชิกเพื่อดูรายการค้างส่ง**")
    return_member_kw = st.text_input(
        "ค้นหาสมาชิก (สำหรับคืน)",
        placeholder="พิมพ์รหัสสมาชิก หรือ ชื่อสมาชิก เช่น M010 หรือ Martha",
        key="return_member_kw",
    )


    rdf = members_df.copy()
    mask_rm = _contains_ignore_case(rdf["member_code"], return_member_kw) | _contains_ignore_case(rdf["name"], return_member_kw)
    rdf = rdf[mask_rm].copy()


    if rdf.empty:
        st.info("ไม่พบสมาชิกตามคำค้น กรุณาลองใหม่")
        return_member_id = None
    else:
        return_member_options = {
            f"{r['member_code']} : {r['name']}": int(r["id"])
            for _, r in rdf.iterrows()
        }
        return_member_label = st.selectbox("รายการสมาชิกที่พบ (สำหรับคืน)", list(return_member_options.keys()), key="return_member_select")
        return_member_id = return_member_options.get(return_member_label)


    if return_member_id:
        active_member_df = model.get_active_borrow_items_by_member(return_member_id)


        if active_member_df.empty:
            st.info("สมาชิกคนนี้ไม่มีรายการยืมค้างส่งในขณะนี้")
        else:
            st.markdown("**2.2 ติ๊กเลือกรายการที่ต้องการคืน (สามารถเลือกได้หลายเล่ม)**")


            show_df = active_member_df.copy()
            show_df.insert(0, "คืน", False)


            edited = st.data_editor(
                show_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "คืน": st.column_config.CheckboxColumn("คืน", help="ติ๊กเพื่อเลือกคืน")
                },
                disabled=[c for c in show_df.columns if c != "คืน"]
            )


            selected_item_ids = edited.loc[edited["คืน"] == True, "item_id"].astype(int).tolist()


            if st.button("📥 ยืนยันการคืนรายการที่เลือก", use_container_width=True, disabled=(len(selected_item_ids) == 0)):
                ok, msgs = controller.return_book_items(
                    item_ids=selected_item_ids,
                    return_staff_user_id=staff_user_id
                )
                if not ok:
                    for m in msgs:
                        st.error("⚠ " + m)
                else:
                    for m in msgs:
                        st.success("✅ " + m)
                    st.rerun()


    st.divider()


    # =========================
    # ส่วนที่ 3: รายการหนังสือค้างส่งทั้งหมด
    # =========================
    st.markdown("### 3) รายการหนังสือค้างส่งทั้งหมด (แสดงชื่อสมาชิก)")


    # ดึงรายการที่ยังไม่คืนทั้งหมด (status = 'borrowed')
    # ฟังก์ชันนี้จะ JOIN ให้เรียบร้อย และมีทั้งชื่อสมาชิก/รหัสสมาชิก/ชื่อหนังสือ/กำหนดส่ง
    all_active_df = model.get_active_borrow_items()


    if all_active_df.empty:
        st.info("ไม่พบรายการหนังสือค้างส่งในขณะนี้")
    else:
        # จัดลำดับคอลัมน์ให้อ่านง่าย (เลือกแสดงเท่าที่จำเป็นต่อการสอน/ใช้งาน)
        show_cols = [
            "รหัสสมาชิก", "ชื่อสมาชิก",
            "รหัสหนังสือ", "ชื่อหนังสือ",
            "วันที่ยืม", "กำหนดส่ง",
            "ผู้ทำรายการยืม", "บทบาทผู้ทำรายการ"
        ]


        # เผื่อบางคอลัมน์ชื่อไม่ตรง (ป้องกัน error) ให้แสดงเฉพาะที่มีจริง
        show_cols = [c for c in show_cols if c in all_active_df.columns]


        st.dataframe(all_active_df[show_cols], use_container_width=True)


        # (ทางเลือก) สรุปจำนวนรายการค้างส่งและจำนวนสมาชิกที่ค้างส่ง
        total_items = len(all_active_df)
        total_members = all_active_df["รหัสสมาชิก"].nunique() if "รหัสสมาชิก" in all_active_df.columns else None


        if total_members is not None:
            st.caption(f"สรุป: รายการค้างส่งทั้งหมด {total_items} รายการ จากสมาชิก {total_members} คน")
        else:
            st.caption(f"สรุป: รายการค้างส่งทั้งหมด {total_items} รายการ")   
    
    
    # =========================
    # ส่วนที่ 4: ประวัติการยืม-คืน
    # =========================
    st.markdown("### 4) ประวัติการยืม-คืน (ค้นหาได้)")


    history_df = model.get_borrow_history(limit=200)


    if history_df.empty:
        st.info("ยังไม่มีประวัติการยืม-คืน")
    else:
        # ช่องค้นหา: ค้นจากบางส่วนของชื่อหนังสือ / รหัสสมาชิก / ชื่อสมาชิก
        hist_kw = st.text_input(
            "ค้นหาประวัติ",
            placeholder="พิมพ์บางส่วนของชื่อหนังสือ หรือ รหัสสมาชิก หรือ ชื่อสมาชิก",
            key="history_search_kw"
        ).strip()


        df = history_df.copy()


        # -----------------------------
        # ตัดคอลัมน์ที่ไม่ต้องแสดง
        # - ไม่แสดง item_id, tx_id
        # - ไม่แสดงคอลัมน์ที่เกี่ยวกับ 'บทบาท'
        # -----------------------------
        drop_cols = []
        for col in df.columns:
            if col in ("item_id", "tx_id"):
                drop_cols.append(col)
            if "บทบาท" in col:  # เช่น "บทบาทผู้ทำรายการยืม"
                drop_cols.append(col)


        if drop_cols:
            df = df.drop(columns=list(set(drop_cols)), errors="ignore")


        # -----------------------------
        # ค้นหาแบบ substring (case-insensitive)
        # คอลัมน์ที่ใช้ค้นหา:
        # - ชื่อหนังสือ
        # - รหัสสมาชิก
        # - ชื่อสมาชิก
        # -----------------------------
        if hist_kw:
            kw = hist_kw.lower()


            def _col_contains(colname: str):
                if colname not in df.columns:
                    # ถ้าไม่มีคอลัมน์นั้น ให้คืน False ทั้งหมด
                    return df.index.to_series().map(lambda _: False)
                return df[colname].fillna("").astype(str).str.lower().str.contains(kw, na=False)


            mask = (
                _col_contains("ชื่อหนังสือ") |
                _col_contains("รหัสสมาชิก") |
                _col_contains("ชื่อสมาชิก")
            )


            df = df[mask].copy()


        # จัดลำดับคอลัมน์ให้อ่านง่าย (แสดงเท่าที่สำคัญ)
        preferred_cols = [
            "รหัสสมาชิก", "ชื่อสมาชิก",
            "รหัสหนังสือ", "ชื่อหนังสือ",
            "วันที่ยืม", "กำหนดส่ง", "วันที่คืน",
            "สถานะ",
            "ผู้ทำรายการยืม", "ผู้ทำรายการคืน"
        ]
        cols_to_show = [c for c in preferred_cols if c in df.columns] + [c for c in df.columns if c not in preferred_cols]
        df = df[cols_to_show]


        if df.empty:
            st.info("ไม่พบข้อมูลตามคำค้น")
        else:
            st.dataframe(df, use_container_width=True)
