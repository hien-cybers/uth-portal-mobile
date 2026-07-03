import tkinter as tk
from tkinter import messagebox
from core import BaseDashboard, CoreManager

class StudentDashboard(BaseDashboard):
    def build_home(self):
        for w in self.main_content.winfo_children(): w.destroy()
        
        card = tk.Frame(self.main_content, bg="white", padx=15, pady=15, bd=0)
        card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(card, text=f"👤 {self.user_obj.fullname} ({self.user_obj.id})", font=("Helvetica Neue", 15, "bold"), bg="white", fg="#1C1C1E").pack(anchor="w")
        tk.Label(card, text=f"Tín chỉ: {self.user_obj.credits}/120 | Nợ: {self.user_obj.debt}đ", font=("Helvetica Neue", 13), fg="#008080", bg="white").pack(anchor="w", pady=(5,0))

        menu_items = [
            ("👤", "Hồ sơ SV", self.view_profile),
            ("📚", "Khung CTĐT", self.view_curriculum),
            ("📅", "Thời khóa biểu", self.view_timetable),
            ("📊", "Bảng điểm", self.view_grades),
            ("📝", "Đăng ký Môn", self.view_registration),
            ("❌", "Hủy Học phần", self.view_cancel),
            ("🎓", "Đơn Tốt nghiệp", self.view_graduation),
            ("💳", "Đóng Học phí", self.view_tuition)
        ]
        self.create_grid_menu(menu_items)

    def view_profile(self):
        self.set_subpage("Hồ sơ Cá nhân")
        self.create_card(self.main_content, self.user_obj.fullname, f"Mã số: {self.user_obj.id}", f"Chuyên ngành: {self.user_obj.major}")

    def view_curriculum(self):
        self.set_subpage("Khung CTĐT")
        scroll = self.create_scroll_canvas()
        for s in CoreManager.get_query("SELECT * FROM SUBJECT"):
            self.create_card(scroll, s['SubjectName'], f"Mã: {s['SubjectID']} | {s['Credits']} Tín chỉ", s['Type'])

    def view_timetable(self):
        self.set_subpage("Thời khóa biểu")
        classes = CoreManager.get_query("SELECT c.ClassID, s.SubjectName, c.Schedule FROM COURSE_CLASS c JOIN REGISTRATION_FORM r ON c.ClassID = r.ClassID JOIN SUBJECT s ON c.SubjectID = s.SubjectID WHERE r.StudentID = ?", (self.user_obj.id,))
        if not classes: tk.Label(self.main_content, text="Chưa có lịch học", bg="#F2F2F7").pack(pady=20)
        scroll = self.create_scroll_canvas()
        for c in classes: self.create_card(scroll, c['SubjectName'], c['ClassID'], c['Schedule'])

    def view_grades(self):
        self.set_subpage("Bảng điểm")
        grades = CoreManager.get_query("SELECT s.SubjectName, a.FinalScore, a.LetterGrade FROM ACADEMIC_RESULT a JOIN REGISTRATION_FORM r ON a.FormID = r.FormID JOIN COURSE_CLASS c ON r.ClassID = c.ClassID JOIN SUBJECT s ON c.SubjectID = s.SubjectID WHERE r.StudentID = ?", (self.user_obj.id,))
        if not grades: tk.Label(self.main_content, text="Chưa có điểm", bg="#F2F2F7").pack(pady=20)
        scroll = self.create_scroll_canvas()
        for g in grades: self.create_card(scroll, g['SubjectName'], f"Điểm hệ 10: {g['FinalScore']}", f"Điểm chữ: {g['LetterGrade']}")

    def view_registration(self):
        self.set_subpage("Đăng ký Môn")
        classes = CoreManager.get_query("SELECT c.ClassID, s.SubjectName, c.MaxCapacity, c.CurrentEnrollment FROM COURSE_CLASS c JOIN SUBJECT s ON c.SubjectID = s.SubjectID WHERE c.Status = 0")
        scroll = self.create_scroll_canvas()
        for c in classes:
            self.create_card(scroll, c['SubjectName'], f"Mã lớp: {c['ClassID']}", f"Sĩ số: {c['CurrentEnrollment']}/{c['MaxCapacity']}", "Đăng ký", lambda cid=c['ClassID']: self.process_reg(cid))

    def view_cancel(self):
        self.set_subpage("Hủy Học phần")
        classes = CoreManager.get_query("SELECT r.FormID, c.ClassID, s.SubjectName FROM REGISTRATION_FORM r JOIN COURSE_CLASS c ON r.ClassID = c.ClassID JOIN SUBJECT s ON c.SubjectID = s.SubjectID WHERE r.StudentID = ?", (self.user_obj.id,))
        scroll = self.create_scroll_canvas()
        for c in classes:
            self.create_card(scroll, c['SubjectName'], f"Mã lớp: {c['ClassID']}", None, "Hủy Môn", lambda fid=c['FormID'], cid=c['ClassID']: self.process_cancel(fid, cid), "#FF3B30")

    def view_graduation(self):
        self.set_subpage("Đơn Tốt nghiệp")
        elig = "Đủ điều kiện" if self.user_obj.credits >= 120 else "Chưa đủ Tín chỉ"
        self.create_card(self.main_content, "Trạng thái", f"Tín chỉ: {self.user_obj.credits}/120 | Nợ: {self.user_obj.debt}", elig, "Nộp Đơn" if elig=="Đủ điều kiện" else None, lambda: CoreManager.execute_query("INSERT INTO GRADUATION_APP VALUES (?, ?, 'Pending')", (f"APP-{self.user_obj.id}", self.user_obj.id)))

    def view_tuition(self):
        self.set_subpage("Học phí")
        self.create_card(self.main_content, "Công nợ Học kỳ", f"Cần đóng: {self.user_obj.debt} VND", None, "Thanh toán ngay" if self.user_obj.debt > 0 else None, self.pay_tuition)

    def process_reg(self, cid):
        cap = CoreManager.get_query("SELECT MaxCapacity, CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = ?", (cid,))[0]
        if cap['CurrentEnrollment'] >= cap['MaxCapacity']: messagebox.showerror("Lỗi", "Lớp đã đầy!"); return
        res = CoreManager.execute_query("INSERT INTO REGISTRATION_FORM VALUES (?, ?, ?, ?)", (f"REG-{self.user_obj.id}-{cid}", self.user_obj.id, cid, "2024-01-01"))
        if res[0]: CoreManager.execute_query("UPDATE COURSE_CLASS SET CurrentEnrollment = CurrentEnrollment + 1 WHERE ClassID = ?", (cid,)); messagebox.showinfo("OK", "Đăng ký thành công!"); self.view_registration()

    def process_cancel(self, fid, cid):
        CoreManager.execute_query("DELETE FROM REGISTRATION_FORM WHERE FormID = ?", (fid,))
        CoreManager.execute_query("UPDATE COURSE_CLASS SET CurrentEnrollment = CurrentEnrollment - 1 WHERE ClassID = ?", (cid,))
        messagebox.showinfo("OK", "Đã hủy lớp!"); self.view_cancel()

    def pay_tuition(self):
        CoreManager.execute_query("UPDATE STUDENT SET Debt = 0 WHERE StudentID = ?", (self.user_obj.id,))
        self.user_obj.debt = 0
        messagebox.showinfo("OK", "Đã thanh toán học phí!"); self.view_tuition()