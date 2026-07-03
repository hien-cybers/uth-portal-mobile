import tkinter as tk
from tkinter import messagebox
from core import BaseDashboard, CoreManager

class AdminDashboard(BaseDashboard):
    def build_home(self):
        for w in self.main_content.winfo_children(): w.destroy()
        tk.Label(self.main_content, text=f"🛠️ {self.user_obj.fullname}", font=("Helvetica Neue", 16, "bold"), bg="#F2F2F7").pack(anchor="w", pady=(0,15))

        menu_items = [
            ("✅", "Duyệt Tốt nghiệp", self.view_audit),
            ("🔑", "Tài khoản", self.view_accounts),
            ("📁", "Hồ sơ SV", self.view_students),
            ("📑", "Khung CTĐT", self.view_subjects),
            ("🏫", "Quản lý Lớp", self.view_classes)
        ]
        self.create_grid_menu(menu_items)

    def view_accounts(self):
        self.set_subpage("Tài khoản")
        accs = CoreManager.get_query("SELECT AccountID, Role, Status FROM ACCOUNT")
        scroll = self.create_scroll_canvas()
        for a in accs: self.create_card(scroll, a['AccountID'], f"Role: {a['Role']}", f"Status: {a['Status']}", "Khóa" if a['Status']=='Active' else "Mở", lambda aid=a['AccountID'], st=a['Status']: self.toggle_acc(aid, st), "#FF3B30" if a['Status']=='Active' else "#34C759")

    def toggle_acc(self, aid, st):
        new_st = 'Locked' if st == 'Active' else 'Active'
        CoreManager.execute_query("UPDATE ACCOUNT SET Status = ? WHERE AccountID = ?", (new_st, aid)); self.view_accounts()

    def view_students(self):
        self.set_subpage("Hồ sơ Sinh viên")
        stus = CoreManager.get_query("SELECT StudentID, Fullname, Major FROM STUDENT")
        scroll = self.create_scroll_canvas()
        for s in stus: self.create_card(scroll, s['Fullname'], s['StudentID'], s['Major'])

    def view_subjects(self):
        self.set_subpage("Khung CTĐT")
        subs = CoreManager.get_query("SELECT * FROM SUBJECT")
        scroll = self.create_scroll_canvas()
        for s in subs: self.create_card(scroll, s['SubjectName'], s['SubjectID'], f"{s['Credits']} TC")

    def view_classes(self):
        self.set_subpage("Quản lý Lớp")
        classes = CoreManager.get_query("SELECT ClassID, Status FROM COURSE_CLASS")
        scroll = self.create_scroll_canvas()
        for c in classes: self.create_card(scroll, c['ClassID'], "Tình trạng:", "Đang mở" if c['Status']==0 else "Đã khóa", "Đổi", lambda cid=c['ClassID'], st=c['Status']: self.toggle_class(cid, st), "#FF9500")

    def toggle_class(self, cid, st):
        new_st = 1 if st == 0 else 0
        CoreManager.execute_query("UPDATE COURSE_CLASS SET Status = ? WHERE ClassID = ?", (new_st, cid)); self.view_classes()

    def view_audit(self):
        self.set_subpage("Duyệt Tốt nghiệp")
        apps = CoreManager.get_query("SELECT * FROM GRADUATION_APP")
        if not apps: tk.Label(self.main_content, text="Không có đơn nào", bg="#F2F2F7").pack(pady=20)
        scroll = self.create_scroll_canvas()
        for a in apps: self.create_card(scroll, f"Mã Đơn: {a['AppID']}", f"Sinh viên: {a['StudentID']}", f"Status: {a['Status']}", "Duyệt", lambda appid=a['AppID']: self.approve_app(appid))

    def approve_app(self, appid):
        CoreManager.execute_query("UPDATE GRADUATION_APP SET Status = 'Approved' WHERE AppID = ?", (appid,))
        messagebox.showinfo("OK", "Đã duyệt bằng tốt nghiệp!"); self.view_audit()