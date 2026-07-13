import sqlite3
import sys
from core import initialize_database

DB_PATH = "uth_portal_final.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    return conn

def seed_baseline(conn):
    rows = [
        (
            "ACCOUNT",
            "AccountID",
            "INSERT OR REPLACE INTO ACCOUNT (AccountID, OwnerID, Password, Role, Status) VALUES (?, ?, ?, ?, ?)",
            [
                ("STU001", "SV01", "123456", "Student", "Active"),
                ("LEC001", "GV01", "123456", "Lecturer", "Active"),
                ("ADM001", "AD01", "123456", "Admin", "Active"),
            ],
        ),
        (
            "STUDENT",
            "StudentID",
            "INSERT OR REPLACE INTO STUDENT (StudentID, Fullname, Major, Credits, GPA, Debt) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("SV01", "Nguyen Minh Khoa", "Cong nghe Thong tin", 118, 3.10, 5000000),
                ("SV120", "Automation Eligible Student", "Cong nghe Thong tin", 120, 3.40, 0),
            ],
        ),
        (
            "LECTURER",
            "LecturerID",
            "INSERT OR REPLACE INTO LECTURER (LecturerID, Fullname) VALUES (?, ?)",
            [("GV01", "Dr. Tran Van Hoang")],
        ),
        (
            "ADMIN",
            "AdminID",
            "INSERT OR REPLACE INTO ADMIN (AdminID, Fullname) VALUES (?, ?)",
            [("AD01", "Quan tri vien He thong")],
        ),
        (
            "SUBJECT",
            "SubjectID",
            "INSERT OR REPLACE INTO SUBJECT (SubjectID, SubjectName, Credits, Type) VALUES (?, ?, ?, ?)",
            [
                ("IT001", "Co so Du lieu", 3, "Bat buoc"),
                ("IT002", "Lap trinh Python", 4, "Bat buoc"),
                ("IT003", "Mang May Tinh", 3, "Tu chon"),
            ],
        ),
        (
            "COURSE_CLASS",
            "ClassID",
            "INSERT OR REPLACE INTO COURSE_CLASS (ClassID, SubjectID, LecturerID, Schedule, MaxCapacity, CurrentEnrollment, Status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("IT001-A", "IT001", "GV01", "T2 (08:00-10:30) - Phong A301", 40, 0, 0),
                ("IT002-B", "IT002", "GV01", "T4 (13:00-15:30) - Phong B205", 40, 0, 0),
                ("IT003-C", "IT003", "GV01", "T2 (08:00-10:30) - Phong C102", 40, 0, 0),
            ],
        ),
    ]

    for _table, _key, sql, values in rows:
        conn.executemany(sql, values)

    conn.execute(
        "INSERT OR REPLACE INTO ACCOUNT (AccountID, OwnerID, Password, Role, Status) VALUES (?, ?, ?, ?, ?)",
        ("STU120", "SV120", "123456", "Student", "Active"),
    )
    conn.commit()

def clean_scenario_data(conn):
    conn.execute("DELETE FROM ACADEMIC_RESULT WHERE FormID LIKE 'AUTO-%' OR FormID LIKE 'REG-SV01-%'")
    conn.execute("DELETE FROM REGISTRATION_FORM WHERE FormID LIKE 'AUTO-%' OR FormID LIKE 'REG-SV01-%'")
    conn.execute("DELETE FROM GRADUATION_APP WHERE AppID LIKE 'AUTO-%' OR AppID IN ('APP-SV01', 'APP-SV120')")
    conn.execute("UPDATE COURSE_CLASS SET CurrentEnrollment = 0, Status = 0 WHERE ClassID IN ('IT001-A', 'IT002-B', 'IT003-C')")
    conn.execute("UPDATE ACCOUNT SET Status = 'Active' WHERE AccountID IN ('STU001', 'STU120', 'LEC001', 'ADM001')")
    conn.execute("UPDATE STUDENT SET Credits = 118, GPA = 3.10, Debt = 5000000 WHERE StudentID = 'SV01'")
    conn.execute("UPDATE STUDENT SET Credits = 120, GPA = 3.40, Debt = 0 WHERE StudentID = 'SV120'")
    conn.commit()

def seed_demo_scenarios(conn):
    conn.execute(
        "INSERT OR REPLACE INTO REGISTRATION_FORM (FormID, StudentID, ClassID, RegDate) VALUES (?, ?, ?, ?)",
        ("AUTO-REG-SV01-IT002-B", "SV01", "IT002-B", "2024-01-01"),
    )
    conn.execute("UPDATE COURSE_CLASS SET CurrentEnrollment = 1 WHERE ClassID = 'IT002-B'")
    
    # ĐÂY LÀ ĐOẠN LỆNH ÔNG LỠ XÓA MẤT NÈ: Làm giả sĩ số đầy 40/40 cho lớp IT003-C
    conn.execute("UPDATE COURSE_CLASS SET CurrentEnrollment = 40 WHERE ClassID = 'IT003-C'")
    
    conn.execute(
        "INSERT OR REPLACE INTO ACADEMIC_RESULT (FormID, ProcessScore, FinalExamScore, FinalScore, LetterGrade) VALUES (?, ?, ?, ?, ?)",
        ("AUTO-REG-SV01-IT002-B", 8.0, 8.5, 8.3, "B+"),
    )
    conn.execute(
        "INSERT OR REPLACE INTO GRADUATION_APP (AppID, StudentID, Status) VALUES (?, ?, ?)",
        ("AUTO-APP-SV120", "SV120", "Pending"),
    )
    conn.commit()

def print_summary(conn):
    for table in [
        "ACCOUNT",
        "STUDENT",
        "LECTURER",
        "ADMIN",
        "SUBJECT",
        "COURSE_CLASS",
        "REGISTRATION_FORM",
        "ACADEMIC_RESULT",
        "GRADUATION_APP",
    ]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")

def main():
    with_scenarios = "--with-scenarios" in sys.argv
    initialize_database()
    with connect() as conn:
        seed_baseline(conn)
        clean_scenario_data(conn)
        if with_scenarios:
            seed_demo_scenarios(conn)
        print(f"Database seeded: {DB_PATH}")
        print_summary(conn)

if __name__ == "__main__":
    main()