from __future__ import annotations

import csv
import tkinter as tk
from pathlib import Path

from tests.helpers.ui_helper import UiAppHelper


def _has(texts: list[str], expected: str) -> bool:
    return any(expected in text for text in texts)


def _login(ui: UiAppHelper, role: str = "Student", username: str = "STU001", password: str = "123456") -> None:
    ui.login(role, username, password)


def _register(ui: UiAppHelper, class_id: str, form_id: str | None = None, student_id: str = "SV01") -> None:
    ui.execute(
        "INSERT OR REPLACE INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)",
        (form_id or f"REG-{student_id}-{class_id}", student_id, class_id, "2026-07-07"),
    )
    ui.execute("UPDATE COURSE_CLASS SET CurrentEnrollment = CurrentEnrollment + 1 WHERE ClassID = ?", (class_id,))


def _add_class(
    ui: UiAppHelper,
    class_id: str,
    subject_id: str = "IT003",
    schedule: str = "T6 (08:00-10:30) - Phong C101",
    capacity: int = 40,
    enrollment: int = 0,
    status: int = 0,
) -> None:
    ui.execute(
        "INSERT OR REPLACE INTO COURSE_CLASS (ClassID, SubjectID, LecturerID, Schedule, MaxCapacity, CurrentEnrollment, Status) "
        "VALUES (?, ?, 'GV01', ?, ?, ?, ?)",
        (class_id, subject_id, schedule, capacity, enrollment, status),
    )


def tc01_ui_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456", detailed=True)
        dashboard = ui.app.frames["StudentDashboard"]
        assert dashboard.user_obj is not None
        assert dashboard.user_obj.id == "SV01"


def tc02_ui_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        login = ui.show_login()
        login.switch_role("Student")
        login.e_usr.delete(0, tk.END)
        login.e_usr.insert(0, "STU001")
        login.e_pwd.delete(0, tk.END)
        login.e_pwd.insert(0, "wrongpass")
        ui.step()
        login.do_login()
        ui.pump()
        assert "1/3" in login.lbl_err.cget("text")


def tc03_ui_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        login = ui.show_login()
        login.switch_role("Lecturer")
        login.e_usr.delete(0, tk.END)
        login.e_usr.insert(0, "STU001")
        login.e_pwd.delete(0, tk.END)
        login.e_pwd.insert(0, "123456")
        ui.step()
        login.do_login()
        ui.pump()
        assert login.lbl_err.cget("text")


def tc04_ui_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        login = ui.show_login()
        login.switch_role("Student")
        for _ in range(3):
            login.e_usr.delete(0, tk.END)
            login.e_usr.insert(0, "STU001")
            login.e_pwd.delete(0, tk.END)
            login.e_pwd.insert(0, "wrongpass")
            ui.step()
            login.do_login()
            ui.pump()
        assert ui.scalar("SELECT Status FROM ACCOUNT WHERE AccountID = 'STU001'") == "Locked"
        assert "khóa" in login.lbl_err.cget("text").lower() or "khoa" in login.lbl_err.cget("text").lower()


def tc05_ui_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.execute("UPDATE ACCOUNT SET Status = 'Locked' WHERE AccountID = 'STU001'")
        ui.login("Student", "STU001", "123456")
        login = ui.app.frames["LoginView"]
        assert login.lbl_err.cget("text")
        assert ui.app.frames["StudentDashboard"].user_obj is None


def tc06_ui_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Lecturer", "LEC001", "123456")
        dashboard = ui.app.frames["LecturerDashboard"]
        assert dashboard.user_obj is not None
        assert dashboard.user_obj.id == "GV01"


def tc07_ui_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        assert dashboard.user_obj is not None
        assert dashboard.user_obj.id == "AD01"


def tc08_ui_student_profile(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.view_profile()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _has(texts, "Nguyen") and _has(texts, "SV01") and _has(texts, "Cong")


def tc09_ui_student_curriculum(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.view_curriculum()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _has(texts, "IT001") and _has(texts, "3")


def tc10_ui_student_timetable(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.view_timetable()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _has(texts, "Co so Du lieu") and _has(texts, "T2") and _has(texts, "Tran")


def tc11_ui_student_transcript(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        ui.execute("INSERT OR REPLACE INTO ACADEMIC_RESULT VALUES ('REG-SV01-IT001-A', 9, 9, 9, 'A')")
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.view_grades()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _has(texts, "9") and _has(texts, "A")


def tc12_ui_student_course_registration(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        before = ui.scalar("SELECT CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = 'IT001-A'")
        dashboard.process_reg("IT001-A")
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE StudentID = 'SV01' AND ClassID = 'IT001-A'") == 1
        assert ui.scalar("SELECT CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = 'IT001-A'") == before + 1


def tc13_ui_student_course_registration(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.process_reg("IT002-B")
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE StudentID = 'SV01'") == 2


def tc14_ui_student_course_registration(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _add_class(ui, "FULLCLS", capacity=1, enrollment=1)
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.process_reg("FULLCLS")
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE ClassID = 'FULLCLS'") == 0
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages)


def tc15_ui_student_course_registration(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _add_class(ui, "SAME-TIME", schedule="T2 (08:00-10:30) - Phong Z999")
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.process_reg("SAME-TIME")
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE ClassID = 'SAME-TIME'") == 0
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages)


def tc16_ui_student_cancel_enrollment(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.process_cancel("REG-SV01-IT001-A", "IT001-A")
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE FormID = 'REG-SV01-IT001-A'") == 0


def tc17_ui_student_graduation(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.view_graduation()
        ui.pump()
        assert not ui.buttons_under(dashboard.main_content)


def tc18_ui_student_tuition(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.view_tuition()
        ui.pump()
        ui.button_containing(dashboard.main_content, "Thanh").invoke()
        ui.pump()
        ui.top_level_button_containing("Kh").invoke()
        ui.pump()
        assert ui.scalar("SELECT Debt FROM STUDENT WHERE StudentID = 'SV01'") == 0


def tc19_ui_student_tuition(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui)
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.view_tuition()
        ui.pump()
        ui.button_containing(dashboard.main_content, "Thanh").invoke()
        ui.pump()
        ui.top_level_button_containing("QR").invoke()
        ui.pump()
        assert ui.scalar("SELECT Debt FROM STUDENT WHERE StudentID = 'SV01'") == 5000000
        assert any(kind == "showinfo" for kind, _title, _msg in ui.messages)


def tc20_ui_lecturer_teaching_schedule(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui, "Lecturer", "LEC001", "123456")
        dashboard = ui.app.frames["LecturerDashboard"]
        dashboard.view_schedule()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _has(texts, "IT001-A") and _has(texts, "T2")


def tc21_ui_lecturer_student_list(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _login(ui, "Lecturer", "LEC001", "123456")
        dashboard = ui.app.frames["LecturerDashboard"]
        dashboard.show_student_list("IT001-A", "Co so Du lieu")
        ui.pump()
        assert _has(ui.label_texts(dashboard.main_content), "Nguyen")


def tc22_ui_lecturer_grade_entry(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _login(ui, "Lecturer", "LEC001", "123456")
        dashboard = ui.app.frames["LecturerDashboard"]
        ui.set_dialog_response("9.0")
        dashboard.enter_grade("REG-SV01-IT001-A", "IT001-A")
        ui.pump()
        assert ui.scalar("SELECT FinalScore FROM ACADEMIC_RESULT WHERE FormID = 'REG-SV01-IT001-A'") == 9.0
        assert ui.scalar("SELECT LetterGrade FROM ACADEMIC_RESULT WHERE FormID = 'REG-SV01-IT001-A'") == "A"


def tc23_ui_lecturer_grade_entry(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _login(ui, "Lecturer", "LEC001", "123456")
        dashboard = ui.app.frames["LecturerDashboard"]
        ui.set_dialog_response("15")
        dashboard.enter_grade("REG-SV01-IT001-A", "IT001-A")
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM ACADEMIC_RESULT WHERE FormID = 'REG-SV01-IT001-A'") == 0
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages)


def tc24_ui_lecturer_grade_entry(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _login(ui, "Lecturer", "LEC001", "123456")
        dashboard = ui.app.frames["LecturerDashboard"]
        ui.set_dialog_response("abc")
        dashboard.enter_grade("REG-SV01-IT001-A", "IT001-A")
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM ACADEMIC_RESULT WHERE FormID = 'REG-SV01-IT001-A'") == 0
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages)


def tc25_ui_admin_accounts(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.toggle_acc("STU001", "Active")
        ui.pump()
        assert ui.scalar("SELECT Status FROM ACCOUNT WHERE AccountID = 'STU001'") == "Locked"


def tc26_ui_admin_students(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.form_add_student()
        ui.pump()
        entries = ui.entries_under(dashboard.main_content)
        entries[0].insert(0, "Test Student")
        entries[1].insert(0, "CNTT")
        ui.buttons_under(dashboard.main_content)[-1].invoke()
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM STUDENT WHERE Fullname = 'Test Student' AND Major = 'CNTT'") == 1


def tc27_ui_admin_students(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.form_add_student()
        ui.pump()
        entries = ui.entries_under(dashboard.main_content)
        entries[0].insert(0, "Test")
        ui.buttons_under(dashboard.main_content)[-1].invoke()
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM STUDENT WHERE Fullname = 'Test'") == 0
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages)


def tc28_ui_admin_students(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.form_edit_student("SV01")
        ui.pump()
        entries = ui.entries_under(dashboard.main_content)
        entries[2].delete(0, tk.END)
        entries[2].insert(0, "2000000")
        ui.buttons_under(dashboard.main_content)[-1].invoke()
        ui.pump()
        assert ui.scalar("SELECT Debt FROM STUDENT WHERE StudentID = 'SV01'") == 2000000


def tc29_ui_admin_students(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.form_edit_student("SV01")
        ui.pump()
        entries = ui.entries_under(dashboard.main_content)
        entries[2].delete(0, tk.END)
        entries[2].insert(0, "abc")
        ui.buttons_under(dashboard.main_content)[-1].invoke()
        ui.pump()
        assert ui.scalar("SELECT Debt FROM STUDENT WHERE StudentID = 'SV01'") == 5000000
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages)


def tc30_ui_admin_students(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.execute("INSERT OR REPLACE INTO STUDENT (StudentID, Fullname, Major, Credits, GPA, Debt) VALUES ('DEL01', 'Delete Me', 'CNTT', 0, 0, 0)")
        ui.execute("INSERT OR REPLACE INTO ACCOUNT VALUES ('DEL01', 'DEL01', '123456', 'Student', 'Active')")
        ui.execute("INSERT OR REPLACE INTO REGISTRATION_FORM VALUES ('REG-DEL01-IT001-A', 'DEL01', 'IT001-A', '2026-07-07')")
        ui.execute("INSERT OR REPLACE INTO ACADEMIC_RESULT VALUES ('REG-DEL01-IT001-A', 8, 8, 8, 'B')")
        ui.execute("INSERT OR REPLACE INTO GRADUATION_APP VALUES ('APP-DEL01', 'DEL01', 'Pending')")
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.delete_student("DEL01")
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM STUDENT WHERE StudentID = 'DEL01'") == 0
        assert ui.scalar("SELECT COUNT(*) FROM ACCOUNT WHERE OwnerID = 'DEL01'") == 0
        assert ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE StudentID = 'DEL01'") == 0
        assert ui.scalar("SELECT COUNT(*) FROM GRADUATION_APP WHERE StudentID = 'DEL01'") == 0
        assert ui.scalar("SELECT COUNT(*) FROM ACADEMIC_RESULT WHERE FormID = 'REG-DEL01-IT001-A'") == 0


def tc31_ui_admin_classes(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.form_add_class()
        ui.pump()
        entries = ui.entries_under(dashboard.main_content)
        for entry, value in zip(entries[:5], ["IT003-D", "IT003", "GV01", "T6 (08:00-10:30)", "40"]):
            entry.insert(0, value)
        ui.buttons_under(dashboard.main_content)[-1].invoke()
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM COURSE_CLASS WHERE ClassID = 'IT003-D'") == 1


def tc32_ui_admin_classes(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.form_add_class()
        ui.pump()
        entries = ui.entries_under(dashboard.main_content)
        for entry, value in zip(entries[:5], ["IT001-A", "IT001", "GV01", "T6 (08:00-10:30)", "40"]):
            entry.insert(0, value)
        ui.buttons_under(dashboard.main_content)[-1].invoke()
        ui.pump()
        assert ui.scalar("SELECT COUNT(*) FROM COURSE_CLASS WHERE ClassID = 'IT001-A'") == 1
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages)


def tc33_ui_admin_classes(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.toggle_class("IT001-A", 0)
        ui.pump()
        assert ui.scalar("SELECT Status FROM COURSE_CLASS WHERE ClassID = 'IT001-A'") == 1
        assert ui.scalar("SELECT CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = 'IT001-A'") == 0
        assert ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE ClassID = 'IT001-A'") == 0


def tc34_ui_admin_graduation(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.execute("INSERT OR REPLACE INTO GRADUATION_APP VALUES ('TEST-APP', 'SV120', 'Pending')")
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        dashboard.approve_app("TEST-APP")
        ui.pump()
        assert ui.scalar("SELECT Status FROM GRADUATION_APP WHERE AppID = 'TEST-APP'") == "Approved"


def tc35_ui_admin_graduation(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.execute("INSERT OR REPLACE INTO GRADUATION_APP VALUES ('TEST-APP', 'SV120', 'Pending')")
        _login(ui, "Admin", "ADM001", "123456")
        dashboard = ui.app.frames["AdminDashboard"]
        ui.set_dialog_response("Outstanding tuition")
        dashboard.reject_app("TEST-APP")
        ui.pump()
        assert ui.scalar("SELECT Status FROM GRADUATION_APP WHERE AppID = 'TEST-APP'") == "Rejected (Outstanding tuition)"


def tc36_ui_lecturer_excel_export(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        _register(ui, "IT001-A")
        export_path = ui.db_path.parent / "student-list.csv"
        ui.set_save_path(export_path)
        _login(ui, "Lecturer", "LEC001", "123456")
        dashboard = ui.app.frames["LecturerDashboard"]
        dashboard.export_to_excel("IT001-A", "Co so Du lieu")
        ui.pump()
        assert export_path.exists()
        rows = list(csv.reader(export_path.open(encoding="utf-8-sig", newline="")))
        assert rows[0] == ["Mã Lớp", "Tên Môn", "Mã SV", "Họ Tên", "Chuyên Ngành"]
        assert any(row[0] == "IT001-A" and row[2] == "SV01" for row in rows[1:])
