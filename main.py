import tkinter as tk
from core import PhoneScreen, AuthManager, initialize_database
from student_view import StudentDashboard
from lecturer_view import LecturerDashboard
from admin_view import AdminDashboard

class SplashScreen(PhoneScreen):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        content = tk.Frame(self.screen, bg="#F2F2F7")
        content.pack(fill=tk.BOTH, expand=True, pady=(20, 10))

        tk.Label(content, text="🏫", font=("Helvetica", 50), bg="#F2F2F7").pack(pady=(10, 15))
        tk.Label(content, text="Hành Trình Học Tập Của\nBạn, Được Thống Nhất", font=("Helvetica Neue", 20, "bold"), fg="#1C1C1E", bg="#F2F2F7", justify="center").pack(pady=(0, 10))
        tk.Label(content, text="Quản lý học vụ đồng bộ — cập nhật tức\nthì, tương tác không trễ.", font=("Helvetica Neue", 13), fg="#8E8E93", bg="#F2F2F7", justify="center").pack(pady=(0, 20))

        center_frame = tk.Frame(content, bg="#F2F2F7")
        center_frame.pack(fill=tk.BOTH, expand=True)
        
        grid = tk.Frame(center_frame, bg="#F2F2F7")
        grid.place(relx=0.5, rely=0.5, anchor=tk.CENTER) 
        
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