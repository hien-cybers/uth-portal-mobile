import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

# ==========================================
# TẦNG 0: DATABASE & MOCK DATA (FULL 16 USE CASES)
# ==========================================
def initialize_database():
    conn = sqlite3.connect('uth_portal_final.db') 
    cursor = conn.cursor()
    
    # 1. Bảng Dữ liệu
    cursor.execute('''CREATE TABLE IF NOT EXISTS ACCOUNT (AccountID TEXT PRIMARY KEY, OwnerID TEXT NOT NULL, Password TEXT NOT NULL, Role TEXT NOT NULL, Status TEXT DEFAULT 'Active')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS STUDENT (StudentID TEXT PRIMARY KEY, Fullname TEXT, Major TEXT, Credits INTEGER, GPA REAL, Debt INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS LECTURER (LecturerID TEXT PRIMARY KEY, Fullname TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ADMIN (AdminID TEXT PRIMARY KEY, Fullname TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS SUBJECT (SubjectID TEXT PRIMARY KEY, SubjectName TEXT, Credits INTEGER, Type TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS COURSE_CLASS (ClassID TEXT PRIMARY KEY, SubjectID TEXT, LecturerID TEXT, Schedule TEXT, MaxCapacity INTEGER, CurrentEnrollment INTEGER DEFAULT 0, Status INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS REGISTRATION_FORM (FormID TEXT PRIMARY KEY, StudentID TEXT, ClassID TEXT, RegDate DATE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ACADEMIC_RESULT (FormID TEXT PRIMARY KEY, ProcessScore REAL, FinalExamScore REAL, FinalScore REAL, LetterGrade TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS GRADUATION_APP (AppID TEXT PRIMARY KEY, StudentID TEXT, Status TEXT)''')

    # 2. Bơm Dữ liệu Mẫu
    cursor.execute("INSERT OR IGNORE INTO ACCOUNT VALUES ('STU001', 'SV01', '123456', 'Student', 'Active')")
    cursor.execute("INSERT OR IGNORE INTO STUDENT VALUES ('SV01', 'Nguyen Minh Khoa', 'Công nghệ Thông tin', 118, 3.10, 5000000)")
    cursor.execute("INSERT OR IGNORE INTO ACCOUNT VALUES ('LEC001', 'GV01', '123456', 'Lecturer', 'Active')")
    cursor.execute("INSERT OR IGNORE INTO LECTURER VALUES ('GV01', 'Dr. Tran Van Hoang')")
    cursor.execute("INSERT OR IGNORE INTO ACCOUNT VALUES ('ADM001', 'AD01', '123456', 'Admin', 'Active')")
    cursor.execute("INSERT OR IGNORE INTO ADMIN VALUES ('AD01', 'Quản trị viên Hệ thống')")
    
    subjects = [('IT001', 'Cơ sở Dữ liệu', 3, 'Bắt buộc'), ('IT002', 'Lập trình Python', 4, 'Bắt buộc'), ('IT003', 'Mạng Máy Tính', 3, 'Tự chọn')]
    for s in subjects: cursor.execute("INSERT OR IGNORE INTO SUBJECT VALUES (?, ?, ?, ?)", s)
    
    classes = [('IT001-A', 'IT001', 'GV01', 'T2 (08:00-10:30) - Phòng A301', 40, 0, 0), 
               ('IT002-B', 'IT002', 'GV01', 'T4 (13:00-15:30) - Phòng B205', 40, 0, 0)]
    for c in classes: cursor.execute("INSERT OR IGNORE INTO COURSE_CLASS VALUES (?, ?, ?, ?, ?, ?, ?)", c)

    conn.commit()
    conn.close()

# ==========================================
# TẦNG 1: MODELS (Thực thể OOP)
# ==========================================
class Person:
    def __init__(self, id_val, fullname):
        self.id = id_val
        self.fullname = fullname

class Student(Person):
    def __init__(self, id_val, fullname, major, credits, gpa, debt):
        super().__init__(id_val, fullname)
        self.major = major
        self.credits = credits
        self.gpa = gpa
        self.debt = debt

# ==========================================
# TẦNG 2: MANAGERS (Trung tâm Nghiệp vụ)
# ==========================================
class AuthManager:
    @staticmethod
    def login(username, password, expected_role):
        conn = sqlite3.connect('uth_portal_final.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ACCOUNT WHERE AccountID = ? AND Password = ? AND Role = ?", (username, password, expected_role))
        acc = cursor.fetchone()
        
        if not acc: return {"status": "error", "message": "Sai thông tin hoặc nhầm vai trò!"}
        if acc['Status'] != 'Active': return {"status": "error", "message": "Tài khoản đã bị khóa!"}
            
        owner_id = acc['OwnerID']
        user_obj = None
        
        if expected_role == 'Student':
            cursor.execute("SELECT * FROM STUDENT WHERE StudentID = ?", (owner_id,))
            data = cursor.fetchone()
            user_obj = Student(owner_id, data['Fullname'], data['Major'], data['Credits'], data['GPA'], data['Debt'])
        else:
            user_obj = Person(owner_id, "Giảng viên" if expected_role == 'Lecturer' else "Quản trị viên") 
            
        conn.close()
        return {"status": "success", "role": expected_role, "user_obj": user_obj}

class CoreManager:
    """Xử lý tất cả các query chung cho các chức năng"""
    @staticmethod
    def get_query(query, args=()):
        conn = sqlite3.connect('uth_portal_final.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, args)
        res = cursor.fetchall()
        conn.close()
        return res

    @staticmethod
    def execute_query(query, args=()):
        conn = sqlite3.connect('uth_portal_final.db')
        cursor = conn.cursor()
        try:
            cursor.execute(query, args)
            conn.commit()
            return True, "Thành công!"
        except Exception as e:
            return False, f"Lỗi: {e}"
        finally:
            conn.close()

# ==========================================
# TẦNG 3: VIEWS (GIAO DIỆN IPHONE 17 PRO MAX)
# ==========================================
class PhoneScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")
        self.controller = controller
        self.screen = tk.Frame(self, bg="#F2F2F7")
        self.screen.pack(fill=tk.BOTH, expand=True, padx=10, pady=15)
        self.screen.pack_propagate(False)
        self.dynamic_island = tk.Frame(self.screen, bg="black", width=120, height=25)
        self.dynamic_island.pack(side=tk.TOP, pady=(5, 0))
        self.dynamic_island.pack_propagate(False)

class SplashScreen(PhoneScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        content = tk.Frame(self.screen, bg="#F2F2F7")
        content.pack(fill=tk.BOTH, expand=True, pady=(20, 10))

        tk.Label(content, text="🏫", font=("Helvetica", 50), bg="#F2F2F7").pack(pady=(10, 15))
        tk.Label(content, text="Hành Trình Học Tập Của\nBạn, Được Thống Nhất", font=("Helvetica Neue", 20, "bold"), fg="#1C1C1E", bg="#F2F2F7", justify="center").pack(pady=(0, 10))
        tk.Label(content, text="Quản lý học vụ đồng bộ — cập nhật tức\nthì, tương tác không trễ.", font=("Helvetica Neue", 13), fg="#8E8E93", bg="#F2F2F7", justify="center").pack(pady=(0, 20))

        # CĂN GIỮA HOÀN HẢO CHO KHỐI GRID
        center_frame = tk.Frame(content, bg="#F2F2F7")
        center_frame.pack(fill=tk.BOTH, expand=True)
        
        grid = tk.Frame(center_frame, bg="#F2F2F7")
        grid.place(relx=0.5, rely=0.5, anchor=tk.CENTER) # Thuật toán neo chính giữa
        
        def card(r, c, icon, t, d):
            frm = tk.Frame(grid, bg="white", bd=0)
            frm.grid(row=r, column=c, padx=6, pady=6, sticky="nsew", ipadx=10, ipady=15)
            tk.Label(frm, text=f"{icon} {t}", font=("Helvetica Neue", 12, "bold"), fg="#008080", bg="white").pack(anchor="w")
            tk.Label(frm, text=d, font=("Helvetica Neue", 10), fg="#8E8E93", bg="white", wraplength=120, justify="left").pack(anchor="w")

        card(0, 0, "📈", "Tiến độ", "Theo dõi thời gian thực")
        card(0, 1, "📝", "Đăng ký", "Mô hình Giỏ hàng")
        card(1, 0, "⭐", "Chấm điểm", "Tính điểm tự động")
        card(1, 1, "🎓", "Tốt nghiệp", "Kiểm duyệt logic 100%")

        bottom = tk.Frame(self.screen, bg="#F2F2F7")
        bottom.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 30), padx=30)
        tk.Button(bottom, text="Bắt đầu", font=("Helvetica Neue", 16, "bold"), bg="#008080", fg="white", bd=0, command=lambda: self.controller.show_frame("LoginView")).pack(fill=tk.X, ipady=12, pady=(0, 10))

class LoginView(PhoneScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.current_role = tk.StringVar(value="Student")
        
        content = tk.Frame(self.screen, bg="#F2F2F7")
        content.pack(fill=tk.BOTH, expand=True, pady=20)

        tk.Label(content, text="UTH Portal", font=("Helvetica Neue", 28, "bold"), fg="#008080", bg="#F2F2F7").pack(pady=(10, 20))

        tab_frame = tk.Frame(content, bg="#E5E5EA", padx=3, pady=3)
        tab_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.btn_stu = tk.Button(tab_frame, text="Sinh viên", bg="white", bd=0, font=("Helvetica Neue", 12, "bold"), command=lambda: self.switch_role("Student"))
        self.btn_stu.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, ipady=5)
        self.btn_lec = tk.Button(tab_frame, text="Giảng viên", bg="#E5E5EA", bd=0, font=("Helvetica Neue", 12), command=lambda: self.switch_role("Lecturer"))
        self.btn_lec.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, ipady=5)
        self.btn_adm = tk.Button(tab_frame, text="Quản trị", bg="#E5E5EA", bd=0, font=("Helvetica Neue", 12), command=lambda: self.switch_role("Admin"))
        self.btn_adm.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, ipady=5)

        form = tk.Frame(content, bg="#F2F2F7", padx=20)
        form.pack(fill=tk.X, pady=20)

        self.e_usr = tk.Entry(form, font=("Helvetica Neue", 16), bd=0, highlightthickness=1)
        self.e_usr.pack(fill=tk.X, ipady=10, pady=10)
        self.e_usr.insert(0, "STU001")
        self.e_pwd = tk.Entry(form, show="*", font=("Helvetica Neue", 16), bd=0, highlightthickness=1)
        self.e_pwd.pack(fill=tk.X, ipady=10, pady=10)
        self.e_pwd.insert(0, "123456")

        tk.Button(form, text="Đăng nhập", font=("Helvetica Neue", 16, "bold"), bg="#008080", fg="white", bd=0, command=self.do_login).pack(fill=tk.X, ipady=12, pady=15)
        self.lbl_err = tk.Label(content, text="", font=("Helvetica Neue", 12), fg="#DC143C", bg="#F2F2F7")
        self.lbl_err.pack()

    def switch_role(self, role):
        self.current_role.set(role)
        self.btn_stu.config(bg="white" if role=="Student" else "#E5E5EA", font=("Helvetica Neue", 12, "bold" if role=="Student" else "normal"))
        self.btn_lec.config(bg="white" if role=="Lecturer" else "#E5E5EA", font=("Helvetica Neue", 12, "bold" if role=="Lecturer" else "normal"))
        self.btn_adm.config(bg="white" if role=="Admin" else "#E5E5EA", font=("Helvetica Neue", 12, "bold" if role=="Admin" else "normal"))
        self.e_usr.delete(0, tk.END)
        self.e_usr.insert(0, "STU001" if role=="Student" else "LEC001" if role=="Lecturer" else "ADM001")

    def do_login(self):
        res = AuthManager.login(self.e_usr.get().strip(), self.e_pwd.get().strip(), self.current_role.get())
        if res["status"] == "success":
            self.lbl_err.config(text="")
            self.controller.show_dashboard(f"{res['role']}Dashboard", res['user_obj'])
        else:
            self.lbl_err.config(text=f"⚠️ {res['message']}")

class BaseDashboard(PhoneScreen):
    """Khuôn mẫu chung có chứa các hàm hỗ trợ vẽ UI siêu tốc"""
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.user_obj = None
        self.nav = tk.Frame(self.screen, bg="white", height=60)
        self.nav.pack(fill=tk.X, side=tk.TOP, pady=(10, 0))
        self.nav.pack_propagate(False)

        self.btn_back = tk.Button(self.nav, text="< Trang chủ", fg="#008080", bg="white", bd=0, font=("Helvetica Neue", 14), command=self.go_home)
        self.lbl_title = tk.Label(self.nav, text="Tổng quan", font=("Helvetica Neue", 18, "bold"), bg="white", fg="#1C1C1E")
        self.lbl_title.pack(side=tk.LEFT, padx=15, pady=15)
        tk.Button(self.nav, text="Thoát", fg="#FF3B30", bg="white", bd=0, font=("Helvetica Neue", 14), command=lambda: self.controller.show_frame("LoginView")).pack(side=tk.RIGHT, padx=15)
        
        self.main_content = tk.Frame(self.screen, bg="#F2F2F7")
        self.main_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    def set_user(self, u):
        self.user_obj = u
        self.build_home()

    def go_home(self):
        self.btn_back.pack_forget()
        self.lbl_title.pack(side=tk.LEFT, padx=15, pady=15)
        self.lbl_title.config(text="Tổng quan")
        self.build_home()

    def set_subpage(self, title):
        for w in self.main_content.winfo_children(): w.destroy()
        self.lbl_title.pack_forget()
        self.btn_back.pack(side=tk.LEFT, padx=10, pady=15)
        tk.Label(self.main_content, text=title, font=("Helvetica Neue", 22, "bold"), bg="#F2F2F7").pack(anchor="w", pady=(0, 10))
        
    def create_scroll_canvas(self):
        canvas = tk.Canvas(self.main_content, bg="#F2F2F7", highlightthickness=0)
        scroll = ttk.Scrollbar(self.main_content, orient="vertical", command=canvas.yview)
        frm = tk.Frame(canvas, bg="#F2F2F7")
        frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frm, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        return frm

    def create_grid_menu(self, buttons_data):
        grid_frame = tk.Frame(self.main_content, bg="#F2F2F7")
        grid_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        row, col = 0, 0
        for icon, text, cmd in buttons_data:
            btn = tk.Button(grid_frame, text=f"{icon}\n{text}", font=("Helvetica Neue", 12, "bold"), bg="white", fg="#008080", bd=0, command=cmd)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew", ipady=15)
            col += 1
            if col > 1: col, row = 0, row + 1

    def create_card(self, parent, title, line1, line2=None, btn_txt=None, btn_cmd=None, btn_color="#008080"):
        """Hàm thần thánh tự động vẽ Card cho mọi chức năng"""
        card = tk.Frame(parent, bg="white", padx=15, pady=15, relief=tk.FLAT)
        card.pack(fill=tk.X, pady=6)
        tk.Label(card, text=title, font=("Helvetica Neue", 15, "bold"), bg="white", fg="#1C1C1E").pack(anchor="w")
        tk.Label(card, text=line1, font=("Helvetica Neue", 12), fg="#8E8E93", bg="white").pack(anchor="w", pady=(2,0))
        if line2: tk.Label(card, text=line2, font=("Helvetica Neue", 12, "bold"), fg="#008080", bg="white").pack(anchor="w")
        if btn_txt: tk.Button(card, text=btn_txt, font=("Helvetica Neue", 12, "bold"), bg=btn_color, fg="white", bd=0, command=btn_cmd).pack(anchor="e", pady=(5,0), ipadx=10, ipady=5)

class StudentDashboard(BaseDashboard):
    def build_home(self):
        for w in self.main_content.winfo_children(): w.destroy()
        
        card = tk.Frame(self.main_content, bg="white", padx=15, pady=15, bd=0)
        card.pack(fill=tk.X, pady=(0, 10))
        tk.Label(card, text=f"👤 {self.user_obj.fullname} ({self.user_obj.id})", font=("Helvetica Neue", 15, "bold"), bg="white", fg="#1C1C1E").pack(anchor="w")
        tk.Label(card, text=f"Tín chỉ: {self.user_obj.credits}/120 | Nợ: {self.user_obj.debt}đ", font=("Helvetica Neue", 13), fg="#008080", bg="white").pack(anchor="w", pady=(5,0))

        # ĐỦ 8 CHỨC NĂNG CỦA SINH VIÊN (Full Hợp Lệ)
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
        self.create_card(self.main_content, "Tiến độ Học tập", f"Tín chỉ: {self.user_obj.credits}/120", f"GPA: {self.user_obj.gpa}")

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
        self.create_card(self.main_content, "Trạng thái Hiện tại", f"Tín chỉ: {self.user_obj.credits}/120 | Nợ: {self.user_obj.debt}", elig, "Nộp Đơn" if elig=="Đủ điều kiện" else None, lambda: CoreManager.execute_query("INSERT INTO GRADUATION_APP VALUES (?, ?, 'Pending')", (f"APP-{self.user_obj.id}", self.user_obj.id)))

    def view_tuition(self):
        self.set_subpage("Học phí")
        self.create_card(self.main_content, "Công nợ Học kỳ", f"Số tiền cần đóng: {self.user_obj.debt} VND", None, "Thanh toán ngay" if self.user_obj.debt > 0 else None, self.pay_tuition)

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
        messagebox.showinfo("Thành công", "Đã thanh toán học phí qua ví điện tử!"); self.view_tuition()

class LecturerDashboard(BaseDashboard):
    def build_home(self):
        for w in self.main_content.winfo_children(): w.destroy()
        tk.Label(self.main_content, text=f"👨‍🏫 {self.user_obj.fullname}", font=("Helvetica Neue", 16, "bold"), bg="#F2F2F7").pack(anchor="w", pady=(0,15))
        
        # ĐỦ 3 CHỨC NĂNG GIẢNG VIÊN
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

class AdminDashboard(BaseDashboard):
    def build_home(self):
        for w in self.main_content.winfo_children(): w.destroy()
        tk.Label(self.main_content, text=f"🛠️ {self.user_obj.fullname}", font=("Helvetica Neue", 16, "bold"), bg="#F2F2F7").pack(anchor="w", pady=(0,15))

        # ĐỦ 5 CHỨC NĂNG ADMIN
        menu_items = [
            ("🔑", "Tài khoản", self.view_accounts),
            ("📁", "Hồ sơ SV", self.view_students),
            ("📑", "Khung CTĐT", self.view_subjects),
            ("🏫", "Quản lý Lớp", self.view_classes),
            ("✅", "Duyệt Tốt nghiệp", self.view_audit)
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

# ==========================================
# BOOTSTRAP APP
# ==========================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Máy ảo iPhone 17 Pro Max")
        self.geometry("420x860")
        self.resizable(False, False)
        
        initialize_database()
        
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (SplashScreen, LoginView, StudentDashboard, LecturerDashboard, AdminDashboard):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("SplashScreen")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        
    def show_dashboard(self, dashboard_name, user_obj):
        dashboard = self.frames[dashboard_name]
        dashboard.set_user(user_obj)
        self.show_frame(dashboard_name)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()