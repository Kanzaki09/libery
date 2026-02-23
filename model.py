import sqlite3
import pandas as pd

DB_PATH = "library.db"


# ============================================================
# DB Connection (SAFE for Streamlit)
# ============================================================
def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False,
        isolation_level=None  # autocommit mode
    )
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


# ============================================================
# Books
# ============================================================
def insert_book(title, author):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO books (title, author, status) VALUES (?, ?, 'available')",
        (title, author)
    )
    conn.commit()
    conn.close()


def fetch_books():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, title, author, status FROM books ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


def get_all_books():
    return fetch_books()


def update_book(book_id, title, author):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE books SET title = ?, author = ? WHERE id = ?",
        (title, author, int(book_id))
    )
    conn.commit()
    conn.close()


def delete_book(book_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id = ?", (int(book_id),))
    conn.commit()
    conn.close()


def set_book_status(book_id: int, status: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE books SET status = ? WHERE id = ?",
        (status, int(book_id))
    )
    conn.commit()
    conn.close()


def get_available_books() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, title, author FROM books WHERE status = 'available' ORDER BY id DESC",
        conn
    )
    conn.close()
    return df


# ============================================================
# Members
# ============================================================
def insert_member(member_code, name, gender, email, phone, is_active):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO members (member_code, name, gender, email, phone, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (member_code, name, gender, email, phone, 1 if is_active else 0)
    )
    conn.commit()
    conn.close()


def fetch_members():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT id, member_code, name, gender, email, phone, is_active, create_at
        FROM members
        ORDER BY id DESC
        """,
        conn
    )
    conn.close()
    return df


def get_all_members():
    return fetch_members()


def get_active_members() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT id, member_code, name
        FROM members
        WHERE is_active = 1
        ORDER BY id DESC
        """,
        conn
    )
    conn.close()
    return df

def member_code_exists(member_code: str) -> bool:
    """
    ตรวจสอบว่ามีรหัสสมาชิก (member_code) นี้ในระบบแล้วหรือไม่
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM members WHERE member_code = ? LIMIT 1",
        (member_code,)
    )

    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def email_exists(email: str) -> bool:
    """
    ตรวจสอบว่า email นี้ถูกใช้แล้วหรือไม่
    (ถ้าไม่กรอก email ให้ถือว่ายังไม่ซ้ำ)
    """
    if not email:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM members WHERE email = ? LIMIT 1",
        (email.strip(),)
    )

    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def update_member(member_id, member_code, name, gender, email, phone, is_active):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        UPDATE members
        SET
            member_code = ?,
            name = ?,
            gender = ?,
            email = ?,
            phone = ?,
            is_active = ?
        WHERE id = ?
        """,
        (
            member_code,
            name,
            gender,
            email,
            phone,
            1 if is_active else 0,
            int(member_id)
        )
    )
    conn.commit()
    conn.close()


def delete_member(member_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "DELETE FROM members WHERE id = ?",
        (int(member_id),)
    )
    conn.commit()
    conn.close()


# ============================================================
# Users / Login
# ============================================================
def get_user_auth_row(username: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, username, password_hash, role, is_active
        FROM users
        WHERE username = ?
        """,
        (username.strip(),)
    )
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    user_id, uname, pw_hash, role, is_active = row
    return {
        "id": user_id,
        "username": uname,
        "password_hash": pw_hash,
        "role": role,
        "is_active": int(is_active)
    }

def get_all_users() -> pd.DataFrame:
    """
    ดึงข้อมูลผู้ใช้ทั้งหมด (สำหรับหน้า Admin)
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            id,
            username,
            role,
            CASE is_active
                WHEN 1 THEN 'ใช้งาน'
                ELSE 'ปิดใช้งาน'
            END AS status
        FROM users
        ORDER BY id DESC
        """,
        conn
    )
    conn.close()
    return df

# ============================================================
# Borrow Schema
# ============================================================
def ensure_borrow_schema():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS borrow_tx (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL,
        staff_user_id INTEGER NOT NULL,
        borrow_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        default_due_date TEXT,
        status TEXT NOT NULL DEFAULT 'open',
        note TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS borrow_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        due_date TEXT,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT 'borrowed',
        return_staff_user_id INTEGER
    )
    """)

    conn.commit()
    conn.close()


# ============================================================
# Borrow / Return
# ============================================================
def get_active_borrow_items_by_member(member_id: int) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            bi.id AS item_id,
            m.member_code,
            m.name,
            bk.title,
            bi.due_date,
            tx.borrow_date
        FROM borrow_items bi
        JOIN borrow_tx tx ON tx.id = bi.tx_id
        JOIN members m ON m.id = tx.member_id
        JOIN books bk ON bk.id = bi.book_id
        WHERE bi.status = 'borrowed'
          AND m.id = ?
        ORDER BY bi.id DESC
        """,
        conn,
        params=(int(member_id),)
    )
    conn.close()
    return df


def get_borrow_history(limit: int = 200) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        f"""
        SELECT
            bi.id AS item_id,
            m.member_code AS รหัสสมาชิก,
            m.name AS ชื่อสมาชิก,
            bk.title AS ชื่อหนังสือ,
            tx.borrow_date AS วันที่ยืม,
            bi.due_date AS กำหนดส่ง,
            bi.return_date AS วันที่คืน,
            bi.status AS สถานะ
        FROM borrow_items bi
        JOIN borrow_tx tx ON tx.id = bi.tx_id
        JOIN members m ON m.id = tx.member_id
        JOIN books bk ON bk.id = bi.book_id
        ORDER BY bi.id DESC
        LIMIT {int(limit)}
        """,
        conn
    )
    conn.close()
    return df

def get_active_borrow_items() -> pd.DataFrame:
    """
    ดึงรายการหนังสือที่กำลังถูกยืมอยู่ทั้งหมด (ยังไม่คืน)
    ใช้แสดงในหน้ารวมการยืม
    """
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            bi.id AS item_id,
            m.member_code AS รหัสสมาชิก,
            m.name AS ชื่อสมาชิก,
            bk.title AS ชื่อหนังสือ,
            bi.due_date AS กำหนดส่ง,
            tx.borrow_date AS วันที่ยืม
        FROM borrow_items bi
        JOIN borrow_tx tx ON tx.id = bi.tx_id
        JOIN members m ON m.id = tx.member_id
        JOIN books bk ON bk.id = bi.book_id
        WHERE bi.status = 'borrowed'
        ORDER BY bi.id DESC
        """,
        conn
    )
    conn.close()
    return df



# ============================================================
# Reports
# ============================================================
def get_book_status_summary():
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            status AS สถานะหนังสือ,
            COUNT(*) AS "จำนวน (เล่ม)"
        FROM books
        GROUP BY status
        """,
        conn
    )
    conn.close()
    return df


def get_borrow_summary_by_month(start_date: str, end_date: str):
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT
            strftime('%Y-%m', borrow_date) AS เดือน,
            COUNT(*) AS จำนวนการยืม
        FROM borrow_tx
        WHERE DATE(borrow_date) BETWEEN ? AND ?
        GROUP BY เดือน
        ORDER BY เดือน
        """,
        conn,
        params=[start_date, end_date]
    )
    conn.close()
    return df


def get_borrow_report(start_date: str, end_date: str, status: str):
    conn = get_connection()

    sql = """
        SELECT
            m.member_code AS รหัสสมาชิก,
            m.name AS ชื่อสมาชิก,
            bk.title AS ชื่อหนังสือ,
            tx.borrow_date AS วันที่ยืม,
            bi.due_date AS กำหนดส่ง,
            bi.return_date AS วันที่คืน,
            bi.status AS สถานะ
        FROM borrow_items bi
        JOIN borrow_tx tx ON tx.id = bi.tx_id
        JOIN members m ON m.id = tx.member_id
        JOIN books bk ON bk.id = bi.book_id
        WHERE DATE(tx.borrow_date) BETWEEN ? AND ?
    """

    params = [start_date, end_date]

    if status != "all":
        sql += " AND bi.status = ?"
        params.append(status)

    sql += " ORDER BY tx.borrow_date DESC"

    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def create_borrow_transaction(member_id: int, staff_user_id: int, default_due_date: str | None, book_ids: list[int], note: str | None = None):
    """
    สร้างธุรกรรมการยืม 1 ครั้ง (ยืมได้หลายเล่ม)
    เงื่อนไข:
      - หนังสือทุกเล่มต้องมีสถานะ available
      - หลังบันทึก ต้องอัปเดต books.status = borrowed
    """
    ensure_borrow_schema()

    if not book_ids:
        raise ValueError("ต้องระบุรายการหนังสืออย่างน้อย 1 เล่ม")

    conn = get_connection()
    c = conn.cursor()

    try:
        # ตรวจสอบสถานะหนังสือทั้งหมดก่อน
        q_marks = ",".join(["?"] * len(book_ids))
        c.execute(f"SELECT id, status FROM books WHERE id IN ({q_marks})", tuple(map(int, book_ids)))
        rows = c.fetchall()

        found_ids = {int(r[0]) for r in rows}
        missing = [bid for bid in book_ids if int(bid) not in found_ids]
        if missing:
            raise ValueError(f"ไม่พบหนังสือ id: {missing}")

        not_available = [int(r[0]) for r in rows if (r[1] or "").lower() != "available"]
        if not_available:
            raise ValueError(f"หนังสือบางเล่มไม่พร้อมให้ยืม (status ไม่ใช่ available): {not_available}")

        # เริ่ม transaction
        conn.execute("BEGIN")

        # 1) insert header
        c.execute(
            """
            INSERT INTO borrow_tx (member_id, staff_user_id, default_due_date, status, note)
            VALUES (?, ?, ?, 'open', ?)
            """,
            (int(member_id), int(staff_user_id), default_due_date, note)
        )
        tx_id = c.lastrowid

        # 2) insert items + update book status
        for bid in book_ids:
            c.execute(
                """
                INSERT INTO borrow_items (tx_id, book_id, due_date, status)
                VALUES (?, ?, ?, 'borrowed')
                """,
                (int(tx_id), int(bid), default_due_date)
            )
            c.execute("UPDATE books SET status = 'borrowed' WHERE id = ?", (int(bid),))

        conn.commit()
        return int(tx_id)

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

        # ============================================================
# Users CRUD (สำหรับ Admin)
# ============================================================

def add_user(username: str, password_hash: str, role: str, is_active: int = 1):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO users (username, password_hash, role, is_active)
        VALUES (?, ?, ?, ?)
        """,
        (username.strip(), password_hash, role, int(is_active))
    )
    conn.commit()
    conn.close()


def is_username_exists(username: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT 1 FROM users WHERE username = ? LIMIT 1",
        (username.strip(),)
    )
    exists = c.fetchone() is not None
    conn.close()
    return exists


def update_user_role(user_id: int, role: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET role = ? WHERE id = ?",
        (role, int(user_id))
    )
    conn.commit()
    conn.close()


def update_user_active(user_id: int, is_active: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET is_active = ? WHERE id = ?",
        (int(is_active), int(user_id))
    )
    conn.commit()
    conn.close()
    conn.close()
