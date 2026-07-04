import tkinter as tk
from tkinter import messagebox, filedialog
import csv
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
        self.set_subpage("Lớp của tôi")
        classes = CoreManager.get_query("SELECT c.ClassID, s.SubjectName FROM COURSE_CLASS c JOIN SUBJECT s ON c.SubjectID = s.SubjectID WHERE c.LecturerID = ?", (self.user_obj.id,))
        scroll = self.create_scroll_canvas()
        for c in classes: 
            self.create_card(scroll, c['SubjectName'], f"Lớp: {c['ClassID']}", None, "Xem Danh sách", lambda cid=c['ClassID'], sname=c['SubjectName']: self.show_student_list(cid, sname))

    def show_student_list(self, cid, sname):
        self.set_subpage("Danh sách SV")
        tk.Button(self.main_content, text="⬇️ Xuất File Excel", bg=AppTheme.SUCCESS, fg=AppTheme.BG_CARD, font=AppTheme.BTN_TEXT, bd=0, command=lambda: self.export_to_excel(cid, sname)).pack(fill=tk.X, pady=(0, 10), ipady=8)
        
        students = CoreManager.get_query("SELECT s.StudentID, s.Fullname, s.Major FROM REGISTRATION_FORM r JOIN STUDENT s ON r.StudentID = s.StudentID WHERE r.ClassID = ?", (cid,))
        scroll = self.create_scroll_canvas()
        if not students:
            tk.Label(scroll, text="Lớp chưa có sinh viên", bg=AppTheme.BG_APP, font=AppTheme.BODY_L).pack(pady=20)
        for s in students: 
            self.create_card(scroll, s['Fullname'], f"Mã SV: {s['StudentID']}", f"Ngành: {s['Major']}")

    def export_to_excel(self, cid, sname):
        students = CoreManager.get_query("SELECT s.StudentID, s.Fullname, s.Major FROM REGISTRATION_FORM r JOIN STUDENT s ON r.StudentID = s.StudentID WHERE r.ClassID = ?", (cid,))
        if not students:
            messagebox.showwarning("Trống", "Không có dữ liệu để xuất!")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"DanhSach_{cid}.csv", filetypes=[("Excel/CSV Files", "*.csv")])
        if file_path:
            with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["Mã Lớp", "Tên Môn", "Mã SV", "Họ Tên", "Chuyên Ngành"])
                for s in students:
                    writer.writerow([cid, sname, s['StudentID'], s['Fullname'], s['Major']])
            messagebox.showinfo("Thành công", f"Đã xuất file thành công tại:\n{file_path}")

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