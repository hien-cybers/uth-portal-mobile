import tkinter as tk
from core import PhoneScreen, AuthManager, initialize_database
from student_view import StudentDashboard
from lecturer_view import LecturerDashboard
from admin_view import AdminDashboard
from theme import AppTheme

class SplashScreen(PhoneScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
    
        content = tk.Frame(self.screen, bg=AppTheme.BG_APP)
        content.pack(fill=tk.BOTH, expand=True, pady=(20, 10))

        tk.Label(content, text="🏫", font=("Helvetica", 50), bg=AppTheme.BG_APP).pack(pady=(10, 15))
        
        tk.Label(content, text="Hành Trình Học Tập Của\nBạn, Được Thống Nhất", font=AppTheme.H2, fg=AppTheme.TEXT_MAIN, bg=AppTheme.BG_APP, justify="center").pack(pady=(0, 10))
        tk.Label(content, text="Quản lý học vụ đồng bộ — cập nhật tức\nthì, tương tác không trễ.", font=AppTheme.BODY_L, fg=AppTheme.TEXT_MUTED, bg=AppTheme.BG_APP, justify="center").pack(pady=(0, 20))

        center_frame = tk.Frame(content, bg=AppTheme.BG_APP)
        center_frame.pack(fill=tk.BOTH, expand=True)
        
        grid = tk.Frame(center_frame, bg=AppTheme.BG_APP)
        grid.place(relx=0.5, rely=0.5, anchor=tk.CENTER) 
        
        def card(r, c, icon, t, d):
            frm = tk.Frame(grid, bg=AppTheme.BG_CARD, bd=0)
            frm.grid(row=r, column=c, padx=6, pady=6, sticky="nsew", ipadx=10, ipady=15)
            tk.Label(frm, text=f"{icon} {t}", font=AppTheme.TITLE_M, fg=AppTheme.PRIMARY, bg=AppTheme.BG_CARD).pack(anchor="w")
            tk.Label(frm, text=d, font=AppTheme.BODY_S, fg=AppTheme.TEXT_MUTED, bg=AppTheme.BG_CARD, wraplength=120, justify="left").pack(anchor="w")

        card(0, 0, "📈", "Tiến độ", "Theo dõi thời gian thực")
        card(0, 1, "📝", "Đăng ký", "Mô hình Giỏ hàng")
        card(1, 0, "⭐", "Chấm điểm", "Tính điểm tự động")
        card(1, 1, "🎓", "Tốt nghiệp", "Kiểm duyệt logic 100%")

        bottom = tk.Frame(self.screen, bg=AppTheme.BG_APP)
        bottom.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 30), padx=30)
        tk.Button(bottom, text="Bắt đầu", font=AppTheme.BTN_TEXT, bg=AppTheme.PRIMARY, fg=AppTheme.BG_CARD, bd=0, command=lambda: self.controller.show_frame("LoginView")).pack(fill=tk.X, ipady=12, pady=(0, 10))

class LoginView(PhoneScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.current_role = tk.StringVar(value="Student")
        
        content = tk.Frame(self.screen, bg=AppTheme.BG_APP)
        content.pack(fill=tk.BOTH, expand=True, pady=20)
        tk.Label(content, text="UTH Portal", font=AppTheme.H1, fg=AppTheme.PRIMARY, bg=AppTheme.BG_APP).pack(pady=(10, 20))

        tab_frame = tk.Frame(content, bg=AppTheme.BORDER, padx=3, pady=3)
        tab_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.btn_stu = tk.Button(tab_frame, text="Sinh viên", bg=AppTheme.BG_CARD, bd=0, font=AppTheme.TITLE_M, command=lambda: self.switch_role("Student"))
        self.btn_stu.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, ipady=5)
        self.btn_lec = tk.Button(tab_frame, text="Giảng viên", bg=AppTheme.BORDER, bd=0, font=AppTheme.BODY_M, command=lambda: self.switch_role("Lecturer"))
        self.btn_lec.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, ipady=5)
        self.btn_adm = tk.Button(tab_frame, text="Quản trị", bg=AppTheme.BORDER, bd=0, font=AppTheme.BODY_M, command=lambda: self.switch_role("Admin"))
        self.btn_adm.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, ipady=5)

        form = tk.Frame(content, bg=AppTheme.BG_APP, padx=20)
        form.pack(fill=tk.X, pady=20)

        self.e_usr = tk.Entry(form, font=AppTheme.TITLE_L, bd=0, highlightthickness=1)
        self.e_usr.pack(fill=tk.X, ipady=10, pady=10)
        self.e_usr.insert(0, "STU001")
        
        self.e_pwd = tk.Entry(form, show="*", font=AppTheme.TITLE_L, bd=0, highlightthickness=1)
        self.e_pwd.pack(fill=tk.X, ipady=10, pady=10)
        self.e_pwd.insert(0, "123456")

        tk.Button(form, text="Đăng nhập", font=AppTheme.BTN_TEXT, bg=AppTheme.PRIMARY, fg=AppTheme.BG_CARD, bd=0, command=self.do_login).pack(fill=tk.X, ipady=12, pady=15)
        self.lbl_err = tk.Label(content, text="", font=AppTheme.BODY_M, fg=AppTheme.DANGER, bg=AppTheme.BG_APP)
        self.lbl_err.pack()

    def switch_role(self, role):
        self.current_role.set(role)
        self.btn_stu.config(bg=AppTheme.BG_CARD if role=="Student" else AppTheme.BORDER, font=AppTheme.TITLE_M if role=="Student" else AppTheme.BODY_M)
        self.btn_lec.config(bg=AppTheme.BG_CARD if role=="Lecturer" else AppTheme.BORDER, font=AppTheme.TITLE_M if role=="Lecturer" else AppTheme.BODY_M)
        self.btn_adm.config(bg=AppTheme.BG_CARD if role=="Admin" else AppTheme.BORDER, font=AppTheme.TITLE_M if role=="Admin" else AppTheme.BODY_M)
        self.e_usr.delete(0, tk.END)
        self.e_usr.insert(0, "STU001" if role=="Student" else "LEC001" if role=="Lecturer" else "ADM001")

    def do_login(self):
        res = AuthManager.login(self.e_usr.get().strip(), self.e_pwd.get().strip(), self.current_role.get())
        if res["status"] == "success":
            self.lbl_err.config(text="")
            self.controller.show_dashboard(f"{res['role']}Dashboard", res['user_obj'])
        else:
            self.lbl_err.config(text=f"⚠️ {res['message']}")

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("APP - UTH Portal")
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