import tkinter as tk
from tkinter import messagebox
import random
from core import BaseDashboard, CoreManager
from theme import AppTheme

class AdminDashboard(BaseDashboard):
    def build_home(self):
        for w in self.main_content.winfo_children(): w.destroy()
        tk.Label(self.main_content, text=f"🛠️ {self.user_obj.fullname}", font=AppTheme.TITLE_L, bg=AppTheme.BG_APP, fg=AppTheme.TEXT_MAIN).pack(anchor="w", pady=(0,15))

        menu_items = [
            ("✅", "Duyệt Tốt nghiệp", self.view_audit),
            ("🔑", "Tài khoản", self.view_accounts),
            ("📁", "Quản lý Sinh viên", self.view_students),
            ("📑", "Khung CTĐT", self.view_subjects),
            ("🏫", "Quản lý Lớp", self.view_classes)
        ]
        self.create_grid_menu(menu_items)

    def view_accounts(self):
        self.set_subpage("Tài khoản Hệ thống")
        accs = CoreManager.get_query("SELECT AccountID, Role, Status FROM ACCOUNT")
        scroll = self.create_scroll_canvas()
        for a in accs: self.create_card(scroll, a['AccountID'], f"Role: {a['Role']}", f"Status: {a['Status']}", "Khóa" if a['Status']=='Active' else "Mở", lambda aid=a['AccountID'], st=a['Status']: self.toggle_acc(aid, st), AppTheme.DANGER if a['Status']=='Active' else AppTheme.SUCCESS)

    def toggle_acc(self, aid, st):
        new_st = 'Locked' if st == 'Active' else 'Active'
        CoreManager.execute_query("UPDATE ACCOUNT SET Status = ? WHERE AccountID = ?", (new_st, aid))
        self.view_accounts()

    def view_students(self):
        self.set_subpage("Quản lý Sinh viên")
        
        top_bar = tk.Frame(self.main_content, bg=AppTheme.BG_APP)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        tk.Label(top_bar, text="Danh sách Sinh viên", font=AppTheme.TITLE_M, bg=AppTheme.BG_APP, fg=AppTheme.TEXT_MAIN).pack(side=tk.LEFT)
        tk.Button(top_bar, text="+ Mới", bg=AppTheme.PRIMARY, fg=AppTheme.BG_CARD, font=AppTheme.BODY_L, bd=0, command=self.form_add_student).pack(side=tk.RIGHT, ipadx=15, ipady=5)
        
        stus = CoreManager.get_query("SELECT StudentID, Fullname, Major, Credits, GPA, Debt FROM STUDENT")
        scroll = self.create_scroll_canvas()
        for s in stus: 
            status = "Hoạt động" if s['Debt'] == 0 else "Đình chỉ"
            self.create_card(scroll, s['Fullname'], f"Mã số: {s['StudentID']} | {status}", f"GPA: {s['GPA']} | Tín chỉ: {s['Credits']}")

    def form_add_student(self):
        self.set_subpage("Thêm Sinh viên Mới")
        
        tk.Label(self.main_content, text="Họ và Tên:", bg=AppTheme.BG_APP, font=AppTheme.BODY_L, fg=AppTheme.TEXT_MAIN).pack(anchor="w")
        e_name = tk.Entry(self.main_content, font=AppTheme.TITLE_M, bd=0, highlightthickness=1)
        e_name.pack(fill=tk.X, pady=5, ipady=8)
        
        tk.Label(self.main_content, text="Chuyên ngành:", bg=AppTheme.BG_APP, font=AppTheme.BODY_L, fg=AppTheme.TEXT_MAIN).pack(anchor="w", pady=(10,0))
        e_major = tk.Entry(self.main_content, font=AppTheme.TITLE_M, bd=0, highlightthickness=1)
        e_major.pack(fill=tk.X, pady=5, ipady=8)
        
        def save():
            name, major = e_name.get().strip(), e_major.get().strip()
            if not name or not major: 
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")
                return
                
            new_id = f"STU{random.randint(1000, 9999)}"
            CoreManager.execute_query("INSERT INTO STUDENT (StudentID, Fullname, Major, Credits, GPA, Debt) VALUES (?, ?, ?, 0, 0.0, 0)", (new_id, name, major))
            CoreManager.execute_query("INSERT INTO ACCOUNT (AccountID, OwnerID, Password, Role, Status) VALUES (?, ?, '123456', 'Student', 'Active')", (new_id, new_id))
            
            messagebox.showinfo("Thành công", f"Đã thêm SV thành công!\n- Mã SV: {new_id}\n- Mật khẩu: 123456")
            self.view_students()
            
        tk.Button(self.main_content, text="Lưu & Cấp Tài khoản", bg=AppTheme.PRIMARY, fg=AppTheme.BG_CARD, font=AppTheme.BTN_TEXT, bd=0, command=save).pack(fill=tk.X, pady=20, ipady=12)

    def view_subjects(self):
        self.set_subpage("Khung CTĐT")
        subs = CoreManager.get_query("SELECT * FROM SUBJECT")
        scroll = self.create_scroll_canvas()
        for s in subs: self.create_card(scroll, s['SubjectName'], s['SubjectID'], f"{s['Credits']} TC")

    def view_classes(self):
        self.set_subpage("Quản lý Lớp")
        classes = CoreManager.get_query("SELECT ClassID, Status FROM COURSE_CLASS")
        scroll = self.create_scroll_canvas()
        for c in classes: self.create_card(scroll, c['ClassID'], "Tình trạng:", "Đang mở" if c['Status']==0 else "Đã khóa", "Đổi", lambda cid=c['ClassID'], st=c['Status']: self.toggle_class(cid, st), AppTheme.WARNING)

    def toggle_class(self, cid, st):
        new_st = 1 if st == 0 else 0
        CoreManager.execute_query("UPDATE COURSE_CLASS SET Status = ? WHERE ClassID = ?", (new_st, cid))
        self.view_classes()

    def view_audit(self):
        self.set_subpage("Duyệt Tốt nghiệp")
        apps = CoreManager.get_query("SELECT * FROM GRADUATION_APP")
        if not apps: tk.Label(self.main_content, text="Không có đơn nào", bg=AppTheme.BG_APP, fg=AppTheme.TEXT_MUTED).pack(pady=20)
        scroll = self.create_scroll_canvas()
        for a in apps: self.create_card(scroll, f"Mã Đơn: {a['AppID']}", f"Sinh viên: {a['StudentID']}", f"Status: {a['Status']}", "Duyệt", lambda appid=a['AppID']: self.approve_app(appid))

    def approve_app(self, appid):
        CoreManager.execute_query("UPDATE GRADUATION_APP SET Status = 'Approved' WHERE AppID = ?", (appid,))
        messagebox.showinfo("OK", "Đã duyệt bằng tốt nghiệp!")
        self.view_audit()