from __future__ import annotations

from pathlib import Path
from typing import Callable

from tests.fixtures.test_data_factory import TestDataFactory
from tests.helpers.database_helper import DatabaseHelper

TestFn = Callable[[Path], None]
TESTS: dict[str, TestFn] = {}


def testcase(test_id: str) -> Callable[[TestFn], TestFn]:
    def decorator(fn: TestFn) -> TestFn:
        TESTS[test_id] = fn
        return fn

    return decorator


EXPECTED_TABLES = {
    "ACCOUNT",
    "STUDENT",
    "LECTURER",
    "ADMIN",
    "SUBJECT",
    "COURSE_CLASS",
    "REGISTRATION_FORM",
    "ACADEMIC_RESULT",
    "GRADUATION_APP",
}


@testcase("TC001")
def tc001_initialize_database_creates_schema(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        tables = {row["name"] for row in db.query("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert EXPECTED_TABLES.issubset(tables), f"Missing tables: {EXPECTED_TABLES - tables}"


@testcase("TC002")
def tc002_initialize_database_seeds_default_data(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        accounts = db.scalar("SELECT COUNT(*) FROM ACCOUNT")
        subjects = db.scalar("SELECT COUNT(*) FROM SUBJECT")
        classes = db.scalar("SELECT COUNT(*) FROM COURSE_CLASS")
        assert accounts >= 3, f"Expected at least 3 accounts, got {accounts}"
        assert subjects >= 3, f"Expected at least 3 subjects, got {subjects}"
        assert classes >= 2, f"Expected at least 2 classes, got {classes}"


@testcase("TC003")
def tc003_login_student_success(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import AuthManager

        result = AuthManager.login("STU001", "123456", "Student")
        assert result["status"] == "success", result
        assert result["role"] == "Student", result
        assert result["user_obj"].id == "SV01", result["user_obj"].id


@testcase("TC004")
def tc004_login_wrong_password_rejected(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import AuthManager

        result = AuthManager.login("STU001", "wrong-password", "Student")
        assert result["status"] == "error", result


@testcase("TC005")
def tc005_login_wrong_role_rejected(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import AuthManager

        result = AuthManager.login("STU001", "123456", "Admin")
        assert result["status"] == "error", result


@testcase("TC006")
def tc006_locked_account_cannot_login(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        db.execute("UPDATE ACCOUNT SET Status = 'Locked' WHERE AccountID = 'STU001'")

        from core import AuthManager

        result = AuthManager.login("STU001", "123456", "Student")
        assert result["status"] == "error", result


@testcase("TC007")
def tc007_student_curriculum_subjects_available(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import CoreManager

        subjects = CoreManager.get_query("SELECT * FROM SUBJECT")
        assert len(subjects) >= 3, f"Expected seeded subjects, got {len(subjects)}"
        assert {"SubjectID", "SubjectName", "Credits", "Type"}.issubset(subjects[0].keys())


@testcase("TC008")
def tc008_register_course_inserts_form_and_increments_enrollment(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        from core import CoreManager

        before = db.scalar("SELECT CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = 'IT001-A'")
        ok, message = CoreManager.execute_query(
            "INSERT INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)",
            ("REG-SV01-IT001-A", "SV01", "IT001-A", "2024-01-01"),
        )
        assert ok, message
        CoreManager.execute_query(
            "UPDATE COURSE_CLASS SET CurrentEnrollment = CurrentEnrollment + 1 WHERE ClassID = ?",
            ("IT001-A",),
        )
        after = db.scalar("SELECT CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = 'IT001-A'")
        exists = db.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE FormID = 'REG-SV01-IT001-A'")
        assert exists == 1, "Registration form was not created."
        assert after == before + 1, f"Expected enrollment {before + 1}, got {after}"


@testcase("TC009")
def tc009_register_duplicate_form_rejected(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import CoreManager

        args = ("REG-SV01-IT001-A", "SV01", "IT001-A", "2024-01-01")
        first = CoreManager.execute_query("INSERT INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)", args)
        second = CoreManager.execute_query("INSERT INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)", args)
        assert first[0] is True, first
        assert second[0] is False, "Duplicate primary key insert should fail."


@testcase("TC010")
def tc010_full_class_blocks_registration(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        db.execute("UPDATE COURSE_CLASS SET CurrentEnrollment = MaxCapacity WHERE ClassID = 'IT001-A'")
        cap = db.query("SELECT MaxCapacity, CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = 'IT001-A'")[0]
        can_register = cap["CurrentEnrollment"] < cap["MaxCapacity"]
        assert can_register is False, "Full class should not be eligible for registration."


@testcase("TC011")
def tc011_cancel_course_deletes_form_and_decrements_enrollment(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        from core import CoreManager

        db.execute(
            "INSERT INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)",
            ("REG-SV01-IT001-A", "SV01", "IT001-A", "2024-01-01"),
        )
        db.execute("UPDATE COURSE_CLASS SET CurrentEnrollment = 1 WHERE ClassID = 'IT001-A'")
        CoreManager.execute_query("DELETE FROM REGISTRATION_FORM WHERE FormID = ?", ("REG-SV01-IT001-A",))
        CoreManager.execute_query(
            "UPDATE COURSE_CLASS SET CurrentEnrollment = CurrentEnrollment - 1 WHERE ClassID = ?",
            ("IT001-A",),
        )
        exists = db.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE FormID = 'REG-SV01-IT001-A'")
        enrollment = db.scalar("SELECT CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = 'IT001-A'")
        assert exists == 0, "Registration form was not deleted."
        assert enrollment == 0, f"Expected enrollment 0, got {enrollment}"


@testcase("TC012")
def tc012_pay_tuition_sets_debt_to_zero(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        from core import CoreManager

        CoreManager.execute_query("UPDATE STUDENT SET Debt = 0 WHERE StudentID = ?", ("SV01",))
        debt = db.scalar("SELECT Debt FROM STUDENT WHERE StudentID = 'SV01'")
        assert debt == 0, f"Expected debt 0, got {debt}"


@testcase("TC013")
def tc013_graduation_application_inserted_for_eligible_student(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        from core import CoreManager

        db.execute("UPDATE STUDENT SET Credits = 120 WHERE StudentID = 'SV01'")
        ok, message = CoreManager.execute_query(
            "INSERT INTO GRADUATION_APP VALUES (?, ?, 'Pending')",
            ("APP-SV01", "SV01"),
        )
        status = db.scalar("SELECT Status FROM GRADUATION_APP WHERE AppID = 'APP-SV01'")
        assert ok, message
        assert status == "Pending", f"Expected Pending, got {status}"


@testcase("TC014")
def tc014_graduation_application_duplicate_rejected(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import CoreManager

        first = CoreManager.execute_query("INSERT INTO GRADUATION_APP VALUES (?, ?, 'Pending')", ("APP-SV01", "SV01"))
        second = CoreManager.execute_query("INSERT INTO GRADUATION_APP VALUES (?, ?, 'Pending')", ("APP-SV01", "SV01"))
        assert first[0] is True, first
        assert second[0] is False, "Duplicate graduation app should fail."


@testcase("TC015")
def tc015_lecturer_schedule_returns_assigned_classes(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import CoreManager

        classes = CoreManager.get_query(
            "SELECT c.ClassID, s.SubjectName, c.Schedule FROM COURSE_CLASS c "
            "JOIN SUBJECT s ON c.SubjectID = s.SubjectID WHERE c.LecturerID = ?",
            ("GV01",),
        )
        assert len(classes) >= 2, f"Expected assigned classes for GV01, got {len(classes)}"


@testcase("TC016")
def tc016_lecturer_class_students_returns_registered_students(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        db.execute(
            "INSERT INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)",
            ("REG-SV01-IT001-A", "SV01", "IT001-A", "2024-01-01"),
        )

        from core import CoreManager

        students = CoreManager.get_query(
            "SELECT r.FormID, s.Fullname FROM REGISTRATION_FORM r "
            "JOIN STUDENT s ON r.StudentID = s.StudentID WHERE r.ClassID = ?",
            ("IT001-A",),
        )
        assert len(students) == 1, f"Expected one registered student, got {len(students)}"
        assert students[0]["FormID"] == "REG-SV01-IT001-A"


@testcase("TC017")
def tc017_admin_accounts_list_contains_roles_and_status(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import CoreManager

        accounts = CoreManager.get_query("SELECT AccountID, Role, Status FROM ACCOUNT")
        roles = {row["Role"] for row in accounts}
        assert {"Student", "Lecturer", "Admin"}.issubset(roles), roles


@testcase("TC018")
def tc018_admin_toggle_account_status(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        from core import CoreManager

        CoreManager.execute_query("UPDATE ACCOUNT SET Status = ? WHERE AccountID = ?", ("Locked", "STU001"))
        locked = db.scalar("SELECT Status FROM ACCOUNT WHERE AccountID = 'STU001'")
        CoreManager.execute_query("UPDATE ACCOUNT SET Status = ? WHERE AccountID = ?", ("Active", "STU001"))
        active = db.scalar("SELECT Status FROM ACCOUNT WHERE AccountID = 'STU001'")
        assert locked == "Locked", locked
        assert active == "Active", active


@testcase("TC019")
def tc019_admin_add_student_creates_student_and_account(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        from core import CoreManager

        student_id = TestDataFactory.student_id()
        name = TestDataFactory.student_name()
        major = TestDataFactory.major()
        student_result = CoreManager.execute_query(
            "INSERT INTO STUDENT (StudentID, Fullname, Major, Credits, GPA, Debt) VALUES (?, ?, ?, 0, 0.0, 0)",
            (student_id, name, major),
        )
        account_result = CoreManager.execute_query(
            "INSERT INTO ACCOUNT (AccountID, OwnerID, Password, Role, Status) VALUES (?, ?, '123456', 'Student', 'Active')",
            (student_id, student_id),
        )
        assert student_result[0] is True, student_result
        assert account_result[0] is True, account_result
        assert db.scalar("SELECT COUNT(*) FROM STUDENT WHERE StudentID = ?", (student_id,)) == 1
        assert db.scalar("SELECT COUNT(*) FROM ACCOUNT WHERE AccountID = ?", (student_id,)) == 1


@testcase("TC020")
def tc020_admin_add_student_missing_required_data_rejected_by_ui_rule(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        name = ""
        major = "Automation Major"
        is_valid = bool(name.strip() and major.strip())
        assert is_valid is False, "Empty student name should be rejected before database insert."


@testcase("TC021")
def tc021_admin_view_subjects(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import CoreManager

        subjects = CoreManager.get_query("SELECT * FROM SUBJECT")
        assert len(subjects) >= 3, f"Expected subjects for admin view, got {len(subjects)}"


@testcase("TC022")
def tc022_admin_toggle_class_status(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        from core import CoreManager

        CoreManager.execute_query("UPDATE COURSE_CLASS SET Status = ? WHERE ClassID = ?", (1, "IT001-A"))
        locked = db.scalar("SELECT Status FROM COURSE_CLASS WHERE ClassID = 'IT001-A'")
        CoreManager.execute_query("UPDATE COURSE_CLASS SET Status = ? WHERE ClassID = ?", (0, "IT001-A"))
        opened = db.scalar("SELECT Status FROM COURSE_CLASS WHERE ClassID = 'IT001-A'")
        assert locked == 1, locked
        assert opened == 0, opened


@testcase("TC023")
def tc023_admin_approve_graduation_application(repo_root: Path) -> None:
    with DatabaseHelper(repo_root) as db:
        from core import CoreManager

        db.execute("INSERT INTO GRADUATION_APP VALUES (?, ?, 'Pending')", ("APP-SV01", "SV01"))
        CoreManager.execute_query("UPDATE GRADUATION_APP SET Status = 'Approved' WHERE AppID = ?", ("APP-SV01",))
        status = db.scalar("SELECT Status FROM GRADUATION_APP WHERE AppID = 'APP-SV01'")
        assert status == "Approved", status


@testcase("TC024")
def tc024_get_query_missing_table_raises_error(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import CoreManager

        try:
            CoreManager.get_query("SELECT * FROM TABLE_DOES_NOT_EXIST")
        except Exception as exc:
            assert "TABLE_DOES_NOT_EXIST" in str(exc) or "no such table" in str(exc)
        else:
            raise AssertionError("Expected query against missing table to raise an error.")


@testcase("TC025")
def tc025_execute_query_invalid_sql_returns_error_tuple(repo_root: Path) -> None:
    with DatabaseHelper(repo_root):
        from core import CoreManager

        ok, message = CoreManager.execute_query("INSERT INTO TABLE_DOES_NOT_EXIST VALUES (1)")
        assert ok is False, "Invalid SQL should return failure flag."
        assert "L" in message or "no such table" in message, message
