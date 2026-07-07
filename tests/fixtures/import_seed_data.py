from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SEED_DATA_PATH = Path(__file__).with_name("seed_data.json")

TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "ACCOUNT": ("AccountID", "OwnerID", "Password", "Role", "Status"),
    "STUDENT": ("StudentID", "CurriculumID", "Fullname", "DateOfBirth", "Major", "Credits", "GPA", "Debt"),
    "LECTURER": ("LecturerID", "Fullname", "Department"),
    "ADMIN": ("AdminID", "Fullname"),
    "SUBJECT": ("SubjectID", "SubjectName", "Credits", "Type"),
    "COURSE_CLASS": (
        "ClassID",
        "SubjectID",
        "LecturerID",
        "Semester",
        "Schedule",
        "MaxCapacity",
        "CurrentEnrollment",
        "Status",
    ),
    "REGISTRATION_FORM": ("FormID", "StudentID", "ClassID", "RegDate"),
    "ACADEMIC_RESULT": ("FormID", "ProcessScore", "FinalExamScore", "FinalScore", "LetterGrade"),
    "GRADUATION_APP": ("AppID", "StudentID", "Status"),
}


def load_seed_data(path: Path = SEED_DATA_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def import_seed_data(
    db_path: Path | str,
    *,
    with_scenarios: bool = False,
    seed_path: Path = SEED_DATA_PATH,
) -> None:
    data = load_seed_data(seed_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        clean_scenario_data(conn)
        seed_baseline(conn, data)
        if with_scenarios:
            seed_scenarios(conn, data)
        conn.commit()
    finally:
        conn.close()


def seed_baseline(conn: sqlite3.Connection, data: dict[str, Any]) -> None:
    for table, rows in data.get("baseline", {}).items():
        insert_rows(conn, table, rows)


def seed_scenarios(conn: sqlite3.Connection, data: dict[str, Any]) -> None:
    for table, rows in data.get("scenarios", {}).items():
        insert_rows(conn, table, rows)

    for update in data.get("scenario_updates", []):
        table = update["table"]
        set_values = update["set"]
        where_values = update["where"]
        set_clause = ", ".join(f"{column} = ?" for column in set_values)
        where_clause = " AND ".join(f"{column} = ?" for column in where_values)
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        conn.execute(sql, [*set_values.values(), *where_values.values()])


def insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict[str, Any]]) -> None:
    columns = TABLE_COLUMNS[table]
    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(columns)
    sql = f"INSERT OR REPLACE INTO {table} ({column_list}) VALUES ({placeholders})"
    conn.executemany(sql, [[row.get(column) for column in columns] for row in rows])


def clean_scenario_data(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM ACADEMIC_RESULT WHERE FormID LIKE 'AUTO-%' OR FormID LIKE 'REG-SV01-%' OR FormID LIKE 'FC-%'")
    conn.execute("DELETE FROM REGISTRATION_FORM WHERE FormID LIKE 'AUTO-%' OR FormID LIKE 'REG-SV01-%' OR FormID LIKE 'FC-%'")
    conn.execute("DELETE FROM GRADUATION_APP WHERE AppID LIKE 'AUTO-%' OR AppID LIKE 'FC-%' OR AppID IN ('APP-SV01', 'APP-SV120')")
    conn.execute("DELETE FROM COURSE_CLASS WHERE ClassID LIKE 'FC-%' OR ClassID IN ('IT001-B', 'IT004-C')")
    conn.execute("UPDATE COURSE_CLASS SET CurrentEnrollment = 0, Status = 0 WHERE ClassID IN ('IT001-A', 'IT002-B')")
    conn.execute("UPDATE ACCOUNT SET Status = 'Active' WHERE AccountID IN ('STU001', 'STU120', 'LEC001', 'ADM001', 'ADM002')")
    conn.execute("UPDATE STUDENT SET Credits = 118, GPA = 3.10, Debt = 5000000 WHERE StudentID = 'SV01'")
    conn.execute("UPDATE STUDENT SET Credits = 120, GPA = 3.40, Debt = 0 WHERE StudentID = 'SV120'")


def table_counts(db_path: Path | str) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        return {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in TABLE_COLUMNS
        }
    finally:
        conn.close()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Import JSON seed data into a UTH Portal SQLite database.")
    parser.add_argument("--db", default="uth_portal_final.db", help="SQLite database path.")
    parser.add_argument("--with-scenarios", action="store_true", help="Import scenario rows for demo/test flows.")
    args = parser.parse_args()

    db_path = Path(args.db)
    import_seed_data(db_path, with_scenarios=args.with_scenarios)
    print(f"Seed data imported: {db_path}")
    for table, count in table_counts(db_path).items():
        print(f"{table}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
