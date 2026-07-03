import tkinter as tk
from tkinter import messagebox
from core import BaseDashboard, CoreManager
from theme import AppTheme

class LecturerDashboard(BaseDashboard):
    def build_home(self):
        for w in self.main_content.winfo_children(): w.destroy()
        tk.Label(self.main_content, text=f"👨‍🏫 {self.user_obj.fullname}", font=AppTheme.TITLE_L, bg=AppTheme.BG_APP, fg=AppTheme.TEXT_MAIN).pack(anchor="w", pady=(0,15))
          
        menu_items = [
            ("📅", "Lịch Giảng", self.view_schedule),
            ("👥", "Danh sách SV", self.view_students),
            ("✍️", "Nhập Điểm", self.view_grading)
        ]
        self.create_grid_menu(menu_items)

    def view_schedule(self):
        self.set_subpage("Lịch Giảng dạy")
        classes = CoreManager.get_query("SELECT c.ClassID, s.SubjectName, c.Schedule FROM COURSE_CLASS c JOIN SUBJECT s ON c.SubjectID = s.SubjectID WHERE c.LecturerID = ?", (self.user_obj.id,))
        scroll = self.create_scroll_canvas()
        for c in classes: self.create_card(scroll, c['SubjectName'], c['ClassID'], c['Schedule'])

    def view_students(self):
        self.set_subpage("Danh sách SV")
        self.create_card(self.main_content, "Tính năng Danh sách SV", "Tích hợp chung trong phần Nhập Điểm", "Vui lòng dùng nút Nhập điểm")

    def view_grading(self):
        self.set_subpage("Nhập Điểm")
        classes = CoreManager.get_query("SELECT c.ClassID, s.SubjectName FROM COURSE_CLASS c JOIN SUBJECT s ON c.SubjectID = s.SubjectID WHERE c.LecturerID = ?", (self.user_obj.id,))
        scroll = self.create_scroll_canvas()
        for c in classes: self.create_card(scroll, c['SubjectName'], f"Lớp: {c['ClassID']}", None, "Chọn", lambda cid=c['ClassID']: self.view_class_students(cid))

    def view_class_students(self, cid):
        self.set_subpage(f"SV Lớp {cid}")
        students = CoreManager.get_query("SELECT r.FormID, s.Fullname FROM REGISTRATION_FORM r JOIN STUDENT s ON r.StudentID = s.StudentID WHERE r.ClassID = ?", (cid,))
        scroll = self.create_scroll_canvas()
        for s in students: self.create_card(scroll, s['Fullname'], "Chưa có điểm", None, "Nhập", lambda fid=s['FormID']: messagebox.showinfo("Điểm", f"Form: {fid} - Tự động set điểm A!"))