from __future__ import annotations

import tkinter as tk
from pathlib import Path

from tests.helpers.ui_helper import UiAppHelper
from tests.integration.test_portal_integration import testcase


def _text_contains(texts: list[str], expected: str) -> bool:
    return any(expected in text for text in texts)


@testcase("TC001")
def tc001_ui_open_app_creates_database(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        assert ui.db_path.exists(), "Opening MainApp should create uth_portal_final.db."
        table_count = ui.scalar("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'")
        assert table_count >= 9, f"Expected initialized schema, got {table_count} tables."


@testcase("TC002")
def tc002_ui_start_button_opens_login_page(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.step()
        splash = ui.app.frames["SplashScreen"]
        buttons = ui.buttons_under(splash)
        assert buttons, "Splash screen should contain a start button."
        ui.step()
        buttons[-1].invoke()
        ui.pump()
        login_view = ui.app.frames["LoginView"]
        assert login_view.winfo_ismapped(), "LoginView should be available after clicking start."
        assert login_view.e_usr.get() == "STU001"


@testcase("TC003")
def tc003_ui_login_student_success(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456", detailed=True)
        dashboard = ui.app.frames["StudentDashboard"]
        assert dashboard.user_obj is not None, "Student dashboard did not receive logged-in user."
        assert dashboard.user_obj.id == "SV01", dashboard.user_obj.id


@testcase("TC004")
def tc004_ui_login_wrong_password_shows_error(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        login_view = ui.show_login()
        ui.step()
        login_view.switch_role("Student")
        ui.step()
        login_view.e_usr.delete(0, tk.END)
        login_view.e_usr.insert(0, "STU001")
        login_view.e_pwd.delete(0, tk.END)
        login_view.e_pwd.insert(0, "wrong-password")
        ui.step()
        login_view.do_login()
        ui.pump()
        error_text = login_view.lbl_err.cget("text")
        print(f"[ACTUAL] TC004 - Login error label: {error_text}", flush=True)
        assert error_text, "Expected visible login error message."


@testcase("TC005")
def tc005_ui_login_wrong_role_shows_error(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        login_view = ui.show_login()
        ui.step()
        login_view.switch_role("Admin")
        ui.step()
        login_view.e_usr.delete(0, tk.END)
        login_view.e_usr.insert(0, "STU001")
        login_view.e_pwd.delete(0, tk.END)
        login_view.e_pwd.insert(0, "123456")
        ui.step()
        login_view.do_login()
        ui.pump()
        error_text = login_view.lbl_err.cget("text")
        print(f"[ACTUAL] TC005 - Login error label: {error_text}", flush=True)
        assert error_text, "Expected wrong-role login error message."


@testcase("TC006")
def tc006_ui_locked_account_cannot_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.toggle_acc("STU001", "Active")
        ui.pump()
        ui.step()
        ui.login("Student", "STU001", "123456")
        login_view = ui.app.frames["LoginView"]
        error_text = login_view.lbl_err.cget("text")
        print(f"[ACTUAL] TC006 - Login error label: {error_text}", flush=True)
        assert error_text, "Expected locked-account login error."


@testcase("TC007")
def tc007_ui_student_profile_screen(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.view_profile()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _text_contains(texts, "SV01"), texts


@testcase("TC008")
def tc008_ui_student_curriculum_screen(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.view_curriculum()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _text_contains(texts, "IT001"), texts


@testcase("TC009")
def tc009_ui_student_timetable_empty_state(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.view_timetable()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _text_contains(texts, "Ch") or not ui.buttons_under(dashboard.main_content), texts


@testcase("TC010")
def tc010_ui_student_grades_empty_state(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.view_grades()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _text_contains(texts, "Ch") or not ui.buttons_under(dashboard.main_content), texts


@testcase("TC011")
def tc011_ui_student_registers_first_open_class(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.view_registration()
        ui.pump()
        buttons = ui.buttons_under(dashboard.main_content)
        assert buttons, "Expected at least one registration button."
        ui.step()
        buttons[0].invoke()
        ui.pump()
        registered = ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE StudentID = ?", ("SV01",))
        assert registered == 1, f"Expected one registration form, got {registered}"


@testcase("TC012")
def tc012_ui_student_duplicate_registration_does_not_duplicate(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.process_reg("IT001-A")
        ui.pump()
        ui.step()
        dashboard.process_reg("IT001-A")
        ui.pump()
        registered = ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE StudentID = ? AND ClassID = ?", ("SV01", "IT001-A"))
        assert registered == 1, f"Expected duplicate registration to stay at one row, got {registered}"


@testcase("TC013")
def tc013_ui_full_class_registration_shows_error(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        ui.step()
        ui.scalar("SELECT COUNT(*) FROM COURSE_CLASS")
        conn = __import__("sqlite3").connect(ui.db_path)
        try:
            conn.execute("UPDATE COURSE_CLASS SET CurrentEnrollment = MaxCapacity WHERE ClassID = 'IT001-A'")
            conn.commit()
        finally:
            conn.close()
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.process_reg("IT001-A")
        ui.pump()
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages), ui.messages


@testcase("TC014")
def tc014_ui_student_cancels_registered_class(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.process_reg("IT001-A")
        ui.pump()
        ui.step()
        dashboard.view_cancel()
        ui.pump()
        button = ui.button_containing(dashboard.main_content, "H\u1ee7y")
        ui.step()
        button.invoke()
        ui.pump()
        registered = ui.scalar("SELECT COUNT(*) FROM REGISTRATION_FORM WHERE StudentID = ?", ("SV01",))
        assert registered == 1, f"Expected closed cancellation window to keep one registration, got {registered}"
        assert any(kind == "showwarning" for kind, _title, _msg in ui.messages), ui.messages


@testcase("TC015")
def tc015_ui_student_pays_tuition(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.view_tuition()
        ui.pump()
        button = ui.button_containing(dashboard.main_content, "Thanh")
        ui.step()
        button.invoke()
        ui.pump()
        direct_button = ui.top_level_button_containing("Kh\u1ea3")
        ui.step()
        direct_button.invoke()
        ui.pump()
        debt = ui.scalar("SELECT Debt FROM STUDENT WHERE StudentID = ?", ("SV01",))
        assert debt == 0, f"Expected debt 0, got {debt}"


@testcase("TC016")
def tc016_ui_ineligible_student_has_no_graduation_submit_button(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        ui.step()
        dashboard.view_graduation()
        ui.pump()
        assert not ui.buttons_under(dashboard.main_content), "Ineligible student should not see submit button."


@testcase("TC017")
def tc017_ui_eligible_student_submits_graduation_application(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        conn = __import__("sqlite3").connect(ui.db_path)
        try:
            conn.execute("UPDATE STUDENT SET Credits = 120 WHERE StudentID = 'SV01'")
            conn.commit()
        finally:
            conn.close()
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        dashboard.user_obj.credits = 120
        ui.step()
        dashboard.view_graduation()
        ui.pump()
        buttons = ui.buttons_under(dashboard.main_content)
        assert buttons, "Eligible student should see graduation submit button."
        ui.step()
        buttons[0].invoke()
        ui.pump()
        status = ui.scalar("SELECT Status FROM GRADUATION_APP WHERE StudentID = ?", ("SV01",))
        assert status == "Pending", status


@testcase("TC018")
def tc018_ui_lecturer_schedule_screen(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Lecturer", "LEC001", "123456")
        dashboard = ui.app.frames["LecturerDashboard"]
        ui.step()
        dashboard.view_schedule()
        ui.pump()
        texts = ui.label_texts(dashboard.main_content)
        assert _text_contains(texts, "IT001-A"), texts


@testcase("TC019")
def tc019_ui_lecturer_views_class_students(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.step()
        conn = __import__("sqlite3").connect(ui.db_path)
        try:
            conn.execute("INSERT INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)", ("REG-SV01-IT001-A", "SV01", "IT001-A", "2024-01-01"))
            conn.commit()
        finally:
            conn.close()
        ui.login("Lecturer", "LEC001", "123456")
        lecturer = ui.app.frames["LecturerDashboard"]
        ui.step()
        lecturer.view_class_students("IT001-A")
        ui.pump()
        texts = ui.label_texts(lecturer.main_content)
        assert _text_contains(texts, "Nguyen") or _text_contains(texts, "Khoa"), texts


@testcase("TC020")
def tc020_ui_lecturer_grading_action_shows_message(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.step()
        conn = __import__("sqlite3").connect(ui.db_path)
        try:
            conn.execute("INSERT INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)", ("REG-SV01-IT001-A", "SV01", "IT001-A", "2024-01-01"))
            conn.commit()
        finally:
            conn.close()
        ui.login("Lecturer", "LEC001", "123456")
        lecturer = ui.app.frames["LecturerDashboard"]
        ui.step()
        lecturer.view_class_students("IT001-A")
        ui.pump()
        buttons = ui.buttons_under(lecturer.main_content)
        assert buttons, "Expected grading input button."
        ui.step()
        buttons[0].invoke()
        ui.pump()
        assert any(kind == "showinfo" for kind, _title, _msg in ui.messages), ui.messages


@testcase("TC021")
def tc021_ui_admin_accounts_screen(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.view_accounts()
        ui.pump()
        texts = ui.label_texts(admin.main_content)
        assert _text_contains(texts, "STU001"), texts


@testcase("TC022")
def tc022_ui_admin_locks_student_account(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.view_accounts()
        ui.pump()
        buttons = ui.buttons_under(admin.main_content)
        assert buttons, "Expected lock/unlock account buttons."
        ui.step()
        buttons[0].invoke()
        ui.pump()
        status = ui.scalar("SELECT Status FROM ACCOUNT WHERE AccountID = ?", ("STU001",))
        assert status == "Locked", f"Expected STU001 to be Locked, got {status}"


@testcase("TC023")
def tc023_ui_admin_students_screen(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.view_students()
        ui.pump()
        texts = ui.label_texts(admin.main_content)
        assert _text_contains(texts, "Nguyen") or _text_contains(texts, "Khoa"), texts


@testcase("TC024")
def tc024_ui_admin_adds_student(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.form_add_student()
        ui.pump()
        entries = [child for child in admin.main_content.winfo_children() if isinstance(child, tk.Entry)]
        assert len(entries) >= 2, "Expected name and major entries."
        ui.step()
        entries[0].insert(0, "Automation UI Student")
        entries[1].insert(0, "Automation Major")
        buttons = ui.buttons_under(admin.main_content)
        ui.step()
        buttons[-1].invoke()
        ui.pump()
        count = ui.scalar("SELECT COUNT(*) FROM STUDENT WHERE Fullname = ?", ("Automation UI Student",))
        assert count == 1, f"Expected added student row, got {count}"


@testcase("TC025")
def tc025_ui_admin_add_student_missing_data_shows_error(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.form_add_student()
        ui.pump()
        entries = [child for child in admin.main_content.winfo_children() if isinstance(child, tk.Entry)]
        ui.step()
        entries[1].insert(0, "Automation Major")
        buttons = ui.buttons_under(admin.main_content)
        ui.step()
        buttons[-1].invoke()
        ui.pump()
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages), ui.messages


@testcase("TC026")
def tc026_ui_admin_subjects_screen(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.view_subjects()
        ui.pump()
        texts = ui.label_texts(admin.main_content)
        assert _text_contains(texts, "IT001"), texts


@testcase("TC027")
def tc027_ui_admin_toggles_class_status(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.view_classes()
        ui.pump()
        button = ui.button_containing(admin.main_content, "\u0110\u1ed5i")
        ui.step()
        button.invoke()
        ui.pump()
        status = ui.scalar("SELECT Status FROM COURSE_CLASS WHERE ClassID = ?", ("IT001-A",))
        assert status == 1, f"Expected locked class status 1, got {status}"


@testcase("TC028")
def tc028_ui_admin_approves_graduation_application(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.step()
        conn = __import__("sqlite3").connect(ui.db_path)
        try:
            conn.execute("INSERT INTO GRADUATION_APP VALUES (?, ?, 'Pending')", ("APP-SV01", "SV01"))
            conn.commit()
        finally:
            conn.close()
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.view_audit()
        ui.pump()
        button = ui.button_containing(admin.main_content, "Duy\u1ec7t")
        ui.step()
        button.invoke()
        ui.pump()
        status = ui.scalar("SELECT Status FROM GRADUATION_APP WHERE AppID = ?", ("APP-SV01",))
        assert status == "Approved", status


@testcase("TC029")
def tc029_ui_logout_returns_to_login(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Student", "STU001", "123456")
        dashboard = ui.app.frames["StudentDashboard"]
        buttons = ui.buttons_under(dashboard.nav)
        logout_buttons = [button for button in buttons if "Tho" in str(button.cget("text"))]
        assert logout_buttons, "Expected logout button in dashboard nav."
        ui.step()
        logout_buttons[0].invoke()
        ui.pump()
        login_view = ui.app.frames["LoginView"]
        assert login_view.e_usr.winfo_exists(), "Login view should still exist after logout."


@testcase("TC030")
def tc030_ui_admin_duplicate_class_shows_error(repo_root: Path) -> None:
    with UiAppHelper(repo_root) as ui:
        ui.login("Admin", "ADM001", "123456")
        admin = ui.app.frames["AdminDashboard"]
        ui.step()
        admin.form_add_class()
        ui.pump()
        entries = ui.entries_under(admin.main_content)
        assert len(entries) >= 5, "Expected class form entries."
        values = ["IT001-A", "IT001", "GV01", "T6 (08:00-10:30)", "40"]
        ui.step()
        for entry, value in zip(entries[:5], values):
            entry.delete(0, tk.END)
            entry.insert(0, value)
        button = ui.button_containing(admin.main_content, "L")
        ui.step()
        button.invoke()
        ui.pump()
        class_count = ui.scalar("SELECT COUNT(*) FROM COURSE_CLASS WHERE ClassID = ?", ("IT001-A",))
        assert class_count == 1, f"Expected duplicate ClassID to stay at one row, got {class_count}"
        assert any(kind == "showerror" for kind, _title, _msg in ui.messages), ui.messages
