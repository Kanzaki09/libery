import streamlit as st
import model
from datetime import date
import io
import os
import pandas as pd
import plotly.express as px

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle

# =========================
# Register Thai Font (TH Sarabun New)
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")

pdfmetrics.registerFont(
    TTFont("THSarabun", os.path.join(FONT_DIR, "THSarabunNew.ttf"))
)


def render_report():
    st.subheader("📊 รายงานสรุประบบยืม-คืนหนังสือ")

    # =========================
    # 1) กราฟวงกลม : สถานะหนังสือ
    # =========================
    st.markdown("### 1) สัดส่วนหนังสือตามสถานะ")

    try:
        status_df = model.get_book_status_summary()
    except Exception as e:
        st.error(f"โหลดข้อมูลสถานะหนังสือไม่สำเร็จ: {e}")
        return

    if status_df.empty:
        st.info("ไม่มีข้อมูลหนังสือ")
    else:
        fig = px.pie(
            status_df,
            names="สถานะหนังสือ",
            values="จำนวน (เล่ม)",
            hole=0.4,
            title="สัดส่วนหนังสือตามสถานะ"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(status_df, use_container_width=True)

    st.divider()

    # =========================
    # 2) กราฟแท่ง : จำนวนการยืมรายเดือน
    # =========================
    st.markdown("### 2) จำนวนการยืมรายเดือน")

    col1, col2 = st.columns(2)

    with col1:
        month_start = st.date_input(
            "วันที่เริ่มต้น (กราฟรายเดือน)",
            value=date(2025, 6, 1)
        )

    with col2:
        month_end = st.date_input(
            "วันที่สิ้นสุด (กราฟรายเดือน)",
            value=date.today()
        )

    if month_start > month_end:
        st.warning("วันที่เริ่มต้นต้องไม่มากกว่าวันที่สิ้นสุด")
        return

    monthly_df = model.get_borrow_summary_by_month(
        month_start.isoformat(),
        month_end.isoformat()
    )

    if monthly_df.empty:
        st.info("ไม่พบข้อมูลการยืมในช่วงเวลาที่เลือก")
    else:
        st.bar_chart(monthly_df.set_index("เดือน")["จำนวนการยืม"])
        st.dataframe(monthly_df, use_container_width=True)

    st.divider()

    # ===============================
    # 3) รายการผู้ยืม–คืนทั้งหมด
    # ===============================
    st.markdown("### 3) รายการผู้ยืม–คืนทั้งหมด")

    col1, col2, col3 = st.columns(3)

    with col1:
        report_start = st.date_input(
            "วันที่เริ่มต้น (รายงาน)",
            value=date(2025, 6, 1)
        )

    with col2:
        report_end = st.date_input(
            "วันที่สิ้นสุด (รายงาน)",
            value=date.today()
        )

    with col3:
        status_label = st.selectbox(
            "สถานะการยืม–คืน",
            ["ทั้งหมด", "ยังไม่คืน", "คืนแล้ว"]
        )

    if report_start > report_end:
        st.warning("วันที่เริ่มต้นต้องไม่มากกว่าวันที่สิ้นสุด")
        return

    status_map = {
        "ทั้งหมด": "all",
        "ยังไม่คืน": "borrowed",
        "คืนแล้ว": "returned"
    }

    report_df = model.get_borrow_report(
        report_start.isoformat(),
        report_end.isoformat(),
        status_map[status_label]
    )

    if report_df.empty:
        st.info("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
        return

    st.dataframe(report_df, use_container_width=True)

    # ===============================
    # 4) ส่งออกรายงาน
    # ===============================
    st.markdown("### 4) ส่งออกรายงาน")

    # ---------- CSV ----------
    csv_buffer = io.StringIO()
    report_df.to_csv(csv_buffer, index=False)

    st.download_button(
        "⬇️ ดาวน์โหลดรายงาน (CSV)",
        csv_buffer.getvalue(),
        "borrow_report.csv",
        "text/csv"
    )

    # ---------- Excel ----------
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        report_df.to_excel(writer, index=False, sheet_name="BorrowReport")

    st.download_button(
        "⬇️ ดาวน์โหลดรายงาน (Excel)",
        excel_buffer.getvalue(),
        "borrow_report.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------- PDF (Thai) ----------
    pdf_buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    elements = []

    title_style = ParagraphStyle(
        name="ThaiTitle",
        fontName="THSarabun",
        fontSize=20,
        alignment=1,
        spaceAfter=16
    )

    normal_style = ParagraphStyle(
        name="ThaiNormal",
        fontName="THSarabun",
        fontSize=14,
        spaceAfter=8
    )

    elements.append(
        Paragraph("รายงานการยืม–คืนหนังสือ", title_style)
    )
    elements.append(
        Paragraph(
            f"ช่วงวันที่ {report_start} ถึง {report_end}",
            normal_style
        )
    )

    table_data = [list(report_df.columns)] + report_df.astype(str).values.tolist()

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "THSarabun"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
    ]))

    elements.append(table)
    doc.build(elements)

    st.download_button(
        "⬇️ ดาวน์โหลดรายงาน (PDF)",
        pdf_buffer.getvalue(),
        "borrow_report.pdf",
        "application/pdf"
    )
