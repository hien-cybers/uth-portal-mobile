import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date
from theme import AppTheme

def initialize_database():
    conn = sqlite3.connect('uth_portal_final.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ACCOUNT (AccountID TEXT PRIMARY KEY, OwnerID TEXT NOT NULL, Password TEXT NOT NULL, Role TEXT NOT NULL, Status TEXT DEFAULT 'Active')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS STUDENT (StudentID TEXT PRIMARY KEY, CurriculumID TEXT, Fullname TEXT, DateOfBirth DATE, Major TEXT, Credits INTEGER, GPA REAL, Debt INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS LECTURER (LecturerID TEXT PRIMARY KEY, Fullname TEXT, Department TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ADMIN (AdminID TEXT PRIMARY KEY, Fullname TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS SUBJECT (SubjectID TEXT PRIMARY KEY, SubjectName TEXT, Credits INTEGER, Type TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS COURSE_CLASS (ClassID TEXT PRIMARY KEY, SubjectID TEXT, LecturerID TEXT, Semester TEXT, Schedule TEXT, MaxCapacity INTEGER, CurrentEnrollment INTEGER DEFAULT 0, Status INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS REGISTRATION_FORM (FormID TEXT PRIMARY KEY, StudentID TEXT, ClassID TEXT, RegDate DATE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ACADEMIC_RESULT (FormID TEXT PRIMARY KEY, ProcessScore REAL, FinalExamScore REAL, FinalScore REAL, LetterGrade TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS GRADUATION_APP (AppID TEXT PRIMARY KEY, StudentID TEXT, Status TEXT)''')

    cursor.execute("INSERT OR IGNORE INTO ACCOUNT VALUES ('STU001', 'SV01', '123456', 'Student', 'Active')")
    cursor.execute("INSERT OR IGNORE INTO STUDENT (StudentID, Fullname, Major, Credits, GPA, Debt) VALUES ('SV01', 'Nguyen Minh Khoa', 'Công nghệ Thông tin', 118, 3.10, 5000000)")
    
    cursor.execute("INSERT OR IGNORE INTO ACCOUNT VALUES ('LEC001', 'GV01', '123456', 'Lecturer', 'Active')")
    cursor.execute("INSERT OR IGNORE INTO LECTURER VALUES ('GV01', 'Dr. Tran Van Hoang', 'Khoa Công nghệ Thông tin')")
    
    cursor.execute("INSERT OR IGNORE INTO ACCOUNT VALUES ('ADM001', 'AD01', '123456', 'Admin', 'Active')")
    cursor.execute("INSERT OR IGNORE INTO ADMIN VALUES ('AD01', 'Quản trị viên Hệ thống')")
    
    subjects = [('IT001', 'Cơ sở Dữ liệu', 3, 'Bắt buộc'), ('IT002', 'Lập trình Python', 4, 'Bắt buộc'), ('IT003', 'Mạng Máy Tính', 3, 'Tự chọn')]
    for s in subjects: cursor.execute("INSERT OR IGNORE INTO SUBJECT VALUES (?, ?, ?, ?)", s)
    
    classes = [
        ('IT001-A', 'IT001', 'GV01', 'HK1-2024', 'T2 (08:00-10:30) - Phòng A301', 40, 0, 0), 
        ('IT002-B', 'IT002', 'GV01', 'HK1-2024', 'T4 (13:00-15:30) - Phòng B205', 40, 0, 0)
    ]
    for c in classes: cursor.execute("INSERT OR IGNORE INTO COURSE_CLASS VALUES (?, ?, ?, ?, ?, ?, ?, ?)", c)
    
    conn.commit()
    conn.close()

class Person:
    def __init__(self, id_val, fullname):
        self.id, self.fullname = id_val, fullname

class Student(Person):
    def __init__(self, id_val, fullname, major, curriculum_id, date_of_birth, credits, gpa, debt):
        super().__init__(id_val, fullname)
        self.major, self.credits, self.gpa, self.debt, self.curriculum_id, self.date_of_birth = major, credits, gpa, debt, curriculum_id, date_of_birth 

class Lecturer(Person):
    def __init__(self, id_val, fullname, department):
        super().__init__(id_val, fullname)
        self.department = department

class Admin(Person):
    def __init__(self, id_val, fullname):
        super().__init__(id_val, fullname)

class CourseClass:
    def __init__(self, class_id, subject_id, lecturer_id, semester, schedule, max_capacity, current_enrollment=0, status=0):
        self.class_id, self.subject_id, self.lecturer_id, self.semester, self.schedule, self.max_capacity, self.current_enrollment, self.status = class_id, subject_id, lecturer_id, semester, schedule, max_capacity, current_enrollment, status
    
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
        
        if expected_role == 'Student':
            cursor.execute("SELECT * FROM STUDENT WHERE StudentID = ?", (owner_id,))
            data = cursor.fetchone()
            user_obj = Student(
                owner_id,
                data['Fullname'],
                data['Major'],          
                data['CurriculumID'],   
                data['DateOfBirth'],
                data['Credits'],
                data['GPA'],
                data['Debt']
            )
        elif expected_role == 'Lecturer':
            cursor.execute("SELECT * FROM LECTURER WHERE LecturerID = ?", (owner_id,))
            data = cursor.fetchone()
            user_obj = Lecturer(owner_id, data['Fullname'], data['Department'])
        else:
            cursor.execute("SELECT * FROM ADMIN WHERE AdminID = ?", (owner_id,))
            data = cursor.fetchone()
            user_obj = Admin(owner_id, data['Fullname'])
        conn.close()
        return {"status": "success", "role": expected_role, "user_obj": user_obj}

class CoreManager:
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
        except Exception as e: return False, f"Lỗi: {e}"
        finally: conn.close()

class PhoneScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="black")
        self.controller = controller
        
        self.screen = tk.Frame(self, bg=AppTheme.BG_APP)
        self.screen.pack(fill=tk.BOTH, expand=True, padx=10, pady=15)
        self.screen.pack_propagate(False)
        
        self.dynamic_island = tk.Frame(self.screen, bg="black", width=120, height=25)
        self.dynamic_island.pack(side=tk.TOP, pady=(5, 0))
        self.dynamic_island.pack_propagate(False)

class BaseDashboard(PhoneScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.user_obj = None
        self.nav = tk.Frame(self.screen, bg=AppTheme.BG_CARD, height=60)
        self.nav.pack(fill=tk.X, side=tk.TOP, pady=(10, 0))
        self.nav.pack_propagate(False)

        self.btn_back = tk.Button(self.nav, text="< Trang chủ", fg=AppTheme.PRIMARY, bg=AppTheme.BG_CARD, bd=0, font=AppTheme.BODY_L, command=self.go_home)
        self.lbl_title = tk.Label(self.nav, text="Tổng quan", font=AppTheme.H3, bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_MAIN)
        self.lbl_title.pack(side=tk.LEFT, padx=15, pady=15)
        tk.Button(self.nav, text="Thoát", fg=AppTheme.DANGER, bg=AppTheme.BG_CARD, bd=0, font=AppTheme.BODY_L, command=lambda: self.controller.show_frame("LoginView")).pack(side=tk.RIGHT, padx=15)
        
        self.main_content = tk.Frame(self.screen, bg=AppTheme.BG_APP)
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
        tk.Label(self.main_content, text=title, font=AppTheme.H2, bg=AppTheme.BG_APP).pack(anchor="w", pady=(0, 10))
        
    def create_scroll_canvas(self):
        canvas = tk.Canvas(self.main_content, bg=AppTheme.BG_APP, highlightthickness=0)
        scroll = ttk.Scrollbar(self.main_content, orient="vertical", command=canvas.yview)
        frm = tk.Frame(canvas, bg=AppTheme.BG_APP)
        frm.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frm, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        return frm

    def create_grid_menu(self, buttons_data):
        grid_frame = tk.Frame(self.main_content, bg=AppTheme.BG_APP)
        grid_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)
        row, col = 0, 0
        for icon, text, cmd in buttons_data:
            btn = tk.Button(grid_frame, text=f"{icon}\n{text}", font=AppTheme.TITLE_M, bg=AppTheme.BG_CARD, fg=AppTheme.PRIMARY, bd=0, command=cmd)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew", ipady=15)
            col += 1
            if col > 1: col, row = 0, row + 1

    def create_card(self, parent, title, line1, line2=None, btn_txt=None, btn_cmd=None, btn_color=AppTheme.PRIMARY):
        card = tk.Frame(parent, bg=AppTheme.BG_CARD, padx=15, pady=15, relief=tk.FLAT)
        card.pack(fill=tk.X, pady=6)
        
        tk.Label(card, text=title, font=AppTheme.TITLE_L, bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_MAIN).pack(anchor="w")
        tk.Label(card, text=line1, font=AppTheme.BODY_M, fg=AppTheme.TEXT_MUTED, bg=AppTheme.BG_CARD).pack(anchor="w", pady=(2,0))
        
        if line2: 
            tk.Label(card, text=line2, font=AppTheme.TITLE_S, fg=AppTheme.PRIMARY, bg=AppTheme.BG_CARD).pack(anchor="w")
            
        if btn_txt: 
            tk.Button(card, text=btn_txt, font=AppTheme.BTN_TEXT, bg=btn_color, fg=AppTheme.BG_CARD, bd=0, command=btn_cmd).pack(anchor="e", pady=(5,0), ipadx=10, ipady=5)

    def dummy_action(self):
        messagebox.showinfo("Đang phát triển", "Tính năng này sẽ được cập nhật!")