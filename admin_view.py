import tkinter as tk
from tkinter import messagebox, simpledialog
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
        if aid == self.user_obj.id:
            messagebox.showerror("Lỗi logic", "Bạn không thể tự khóa tài khoản đang đăng nhập của chính mình!")
            return
            
        new_st = 'Locked' if st == 'Active' else 'Active'
        CoreManager.execute_query("UPDATE ACCOUNT SET Status = ? WHERE AccountID = ?", (new_st, aid))
        self.view_accounts()

    def toggle_class(self, cid, st):
        if st == 0: 
            cls_info = CoreManager.get_query("SELECT CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = ?", (cid,))[0]
            if cls_info['CurrentEnrollment'] > 0:
                ans = messagebox.askyesno("Cảnh báo Nghiêm trọng", f"Lớp {cid} đang có {cls_info['CurrentEnrollment']} SV đăng ký.\nViệc khóa lớp sẽ HỦY TOÀN BỘ đăng ký. Tiếp tục?")
                if not ans: return
                forms = CoreManager.get_query("SELECT FormID FROM REGISTRATION_FORM WHERE ClassID = ?", (cid,))
                for f in forms:
                    CoreManager.execute_query("DELETE FROM ACADEMIC_RESULT WHERE FormID = ?", (f['FormID'],))
                    
                CoreManager.execute_query("DELETE FROM REGISTRATION_FORM WHERE ClassID = ?", (cid,))
                CoreManager.execute_query("UPDATE COURSE_CLASS SET CurrentEnrollment = 0 WHERE ClassID = ?", (cid,))
                
        new_st = 1 if st == 0 else 0
        CoreManager.execute_query("UPDATE COURSE_CLASS SET Status = ? WHERE ClassID = ?", (new_st, cid))
        self.view_classes()

    def approve_app(self, appid):
        stu_id = CoreManager.get_query("SELECT StudentID FROM GRADUATION_APP WHERE AppID = ?", (appid,))[0]['StudentID']
        stu = CoreManager.get_query("SELECT Credits, Debt FROM STUDENT WHERE StudentID = ?", (stu_id,))[0]
        
        if stu['Credits'] < 120 or stu['Debt'] > 0:
            messagebox.showerror("Từ chối tự động", f"Sinh viên chưa đủ điều kiện!\n- Tín chỉ: {stu['Credits']}/120\n- Nợ: {stu['Debt']}đ")
            return
            
        CoreManager.execute_query("UPDATE GRADUATION_APP SET Status = 'Approved' WHERE AppID = ?", (appid,))
        messagebox.showinfo("OK", "Đã duyệt bằng tốt nghiệp!")
        self.view_audit()

    def view_students(self):
        self.set_subpage("Quản lý Sinh viên")
        
        top_bar = tk.Frame(self.main_content, bg=AppTheme.BG_APP)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        tk.Label(top_bar, text="Danh sách Sinh viên", font=AppTheme.TITLE_M, bg=AppTheme.BG_APP, fg=AppTheme.TEXT_MAIN).pack(side=tk.LEFT)
        tk.Button(top_bar, text="+ Mới", bg=AppTheme.PRIMARY, fg=AppTheme.BG_CARD, font=AppTheme.BODY_L, bd=0, command=self.form_add_student).pack(side=tk.RIGHT, ipadx=15, ipady=5)
        
        stus = CoreManager.get_query("SELECT StudentID, Fullname, Major, Credits, GPA, Debt FROM STUDENT")
        scroll = self.create_scroll_canvas()
        
        for s in stus: 
            status = "Hoạt động" if s['Debt'] == 0 else f"Nợ: {s['Debt']}đ"
            card = tk.Frame(scroll, bg=AppTheme.BG_CARD, padx=15, pady=15, relief=tk.FLAT)
            card.pack(fill=tk.X, pady=5)
            
            info_frame = tk.Frame(card, bg=AppTheme.BG_CARD)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            tk.Label(info_frame, text=s['Fullname'], font=AppTheme.TITLE_M, bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_MAIN).pack(anchor="w")
            tk.Label(info_frame, text=f"Mã số: {s['StudentID']} | {status}", font=AppTheme.BODY_M, bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_MUTED).pack(anchor="w")
            tk.Label(info_frame, text=f"GPA: {s['GPA']} | Tín chỉ: {s['Credits']}", font=AppTheme.BODY_M, bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_MUTED).pack(anchor="w")
            
            btn_frame = tk.Frame(card, bg=AppTheme.BG_CARD)
            btn_frame.pack(side=tk.RIGHT)
            
            tk.Button(btn_frame, text="Sửa", bg=AppTheme.WARNING, fg=AppTheme.BG_CARD, font=AppTheme.BTN_TEXT, bd=0, command=lambda sid=s['StudentID']: self.form_edit_student(sid)).pack(side=tk.LEFT, padx=5, ipady=5, ipadx=15)
            tk.Button(btn_frame, text="Xóa", bg=AppTheme.DANGER, fg=AppTheme.BG_CARD, font=AppTheme.BTN_TEXT, bd=0, command=lambda sid=s['StudentID']: self.delete_student(sid)).pack(side=tk.LEFT, padx=5, ipady=5, ipadx=15)

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

    def form_edit_student(self, sid):
        self.set_subpage(f"Sửa Hồ Sơ: {sid}")
        stu = CoreManager.get_query("SELECT * FROM STUDENT WHERE StudentID = ?", (sid,))[0]
        
        scroll = self.create_scroll_canvas()
        
        def make_input(label_txt, default_val):
            tk.Label(scroll, text=label_txt, bg=AppTheme.BG_APP, font=AppTheme.BODY_L, fg=AppTheme.TEXT_MAIN).pack(anchor="w", pady=(10,0))
            entry = tk.Entry(scroll, font=AppTheme.TITLE_M, bd=0, highlightthickness=1)
            entry.pack(fill=tk.X, pady=5, ipady=8)
            entry.insert(0, str(default_val))
            return entry

        e_name = make_input("Họ và Tên:", stu['Fullname'])
        e_major = make_input("Chuyên ngành:", stu['Major'])
        e_debt = make_input("Nợ học phí (VNĐ):", stu['Debt'])

        def save_edit():
            name, major, debt = e_name.get().strip(), e_major.get().strip(), e_debt.get().strip()
            if not name or not major or not debt.isdigit():
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin hợp lệ (Nợ phải là số)!")
                return
            
            CoreManager.execute_query("UPDATE STUDENT SET Fullname = ?, Major = ?, Debt = ? WHERE StudentID = ?", (name, major, int(debt), sid))
            messagebox.showinfo("Thành công", f"Đã cập nhật hồ sơ sinh viên {sid}!")
            self.view_students()

        tk.Button(scroll, text="Lưu Cập Nhật", bg=AppTheme.SUCCESS, fg=AppTheme.BG_CARD, font=AppTheme.BTN_TEXT, bd=0, command=save_edit).pack(fill=tk.X, pady=20, ipady=12)

    def delete_student(self, sid):
        ans = messagebox.askyesno("Cảnh báo Nghiêm trọng", f"Bạn có chắc chắn muốn xóa TOÀN BỘ dữ liệu của {sid}?\nHành động này sẽ xóa cả tài khoản, lịch học và bảng điểm của sinh viên này!")
        if ans:
            CoreManager.execute_query("DELETE FROM ACCOUNT WHERE OwnerID = ?", (sid,))
            CoreManager.execute_query("DELETE FROM REGISTRATION_FORM WHERE StudentID = ?", (sid,))
            CoreManager.execute_query("DELETE FROM GRADUATION_APP WHERE StudentID = ?", (sid,))
            CoreManager.execute_query("DELETE FROM STUDENT WHERE StudentID = ?", (sid,))
            messagebox.showinfo("Thành công", f"Đã xóa hoàn toàn sinh viên {sid} khỏi hệ thống.")
            self.view_students()
    def view_subjects(self):
        self.set_subpage("Khung CTĐT (Môn học)")
        
        # Thanh công cụ chứa Tiêu đề và Nút Thêm mới
        top_bar = tk.Frame(self.main_content, bg=AppTheme.BG_APP)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        tk.Label(top_bar, text="Danh sách Môn học", font=AppTheme.TITLE_M, bg=AppTheme.BG_APP, fg=AppTheme.TEXT_MAIN).pack(side=tk.LEFT)
        tk.Button(top_bar, text="+ Môn mới", bg=AppTheme.PRIMARY, fg=AppTheme.BG_CARD, font=AppTheme.BODY_L, bd=0, command=self.form_add_subject).pack(side=tk.RIGHT, ipadx=15, ipady=5)

        subs = CoreManager.get_query("SELECT * FROM SUBJECT")
        scroll = self.create_scroll_canvas()
        
        for s in subs: 
            card = tk.Frame(scroll, bg=AppTheme.BG_CARD, padx=15, pady=15, relief=tk.FLAT)
            card.pack(fill=tk.X, pady=5)
            
            info_frame = tk.Frame(card, bg=AppTheme.BG_CARD)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            tk.Label(info_frame, text=s['SubjectName'], font=AppTheme.TITLE_M, bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_MAIN).pack(anchor="w")
            tk.Label(info_frame, text=f"Mã môn: {s['SubjectID']} | {s['Credits']} Tín chỉ | Loại: {s['Type']}", font=AppTheme.BODY_M, bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_MUTED).pack(anchor="w")
            
            btn_frame = tk.Frame(card, bg=AppTheme.BG_CARD)
            btn_frame.pack(side=tk.RIGHT)
            
            tk.Button(btn_frame, text="Sửa", bg=AppTheme.WARNING, fg=AppTheme.BG_CARD, font=AppTheme.BTN_TEXT, bd=0, command=lambda sid=s['SubjectID']: self.form_edit_subject(sid)).pack(side=tk.LEFT, padx=5, ipady=5, ipadx=15)
            tk.Button(btn_frame, text="Xóa", bg=AppTheme.DANGER, fg=AppTheme.BG_CARD, font=AppTheme.BTN_TEXT, bd=0, command=lambda sid=s['SubjectID']: self.delete_subject(sid)).pack(side=tk.LEFT, padx=5, ipady=5, ipadx=15)

    def view_classes(self):
        self.set_subpage("Quản lý Lớp")
        
        top_bar = tk.Frame(self.main_content, bg=AppTheme.BG_APP)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        tk.Label(top_bar, text="Danh sách Lớp học", font=AppTheme.TITLE_M, bg=AppTheme.BG_APP, fg=AppTheme.TEXT_MAIN).pack(side=tk.LEFT)
        tk.Button(top_bar, text="+ Lớp mới", bg=AppTheme.PRIMARY, fg=AppTheme.BG_CARD, font=AppTheme.BODY_L, bd=0, command=self.form_add_class).pack(side=tk.RIGHT, ipadx=15, ipady=5)

        classes = CoreManager.get_query("SELECT ClassID, Status, CurrentEnrollment, MaxCapacity FROM COURSE_CLASS")
        scroll = self.create_scroll_canvas()
        for c in classes: 
            self.create_card(scroll, c['ClassID'], f"Sĩ số: {c['CurrentEnrollment']}/{c['MaxCapacity']}", "Đang mở" if c['Status']==0 else "Đã khóa", "Đổi", lambda cid=c['ClassID'], st=c['Status']: self.toggle_class(cid, st), AppTheme.WARNING)

    def form_add_class(self):
        self.set_subpage("Tạo Lớp Mới")
        scroll = self.create_scroll_canvas()
        
        def make_input(label_txt):
            tk.Label(scroll, text=label_txt, bg=AppTheme.BG_APP, font=AppTheme.BODY_L, fg=AppTheme.TEXT_MAIN).pack(anchor="w", pady=(10,0))
            entry = tk.Entry(scroll, font=AppTheme.TITLE_M, bd=0, highlightthickness=1)
            entry.pack(fill=tk.X, pady=5, ipady=8)
            return entry

        e_cid = make_input("Mã Lớp (VD: IT004-A):")
        e_sid = make_input("Mã Môn học (VD: IT001):")
        e_lid = make_input("Mã Giảng viên (VD: GV01):")
        e_sch = make_input("Lịch học (VD: T3 (08:00-10:30)):")
        e_cap = make_input("Sĩ số tối đa (VD: 40):")

        def save():
            cid, sid, lid, sch, cap = e_cid.get().strip(), e_sid.get().strip(), e_lid.get().strip(), e_sch.get().strip(), e_cap.get().strip()
            if not all([cid, sid, lid, sch, cap]):
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")
                return
            try:
                CoreManager.execute_query("INSERT INTO COURSE_CLASS (ClassID, SubjectID, LecturerID, Schedule, MaxCapacity, CurrentEnrollment, Status) VALUES (?, ?, ?, ?, ?, 0, 0)", (cid, sid, lid, sch, int(cap)))
                messagebox.showinfo("Thành công", "Đã mở lớp học mới!")
                self.view_classes()
            except Exception as e:
                messagebox.showerror("Lỗi CSDL", "Vui lòng kiểm tra lại. Có thể Mã lớp đã tồn tại!")
                
        tk.Button(scroll, text="Lưu Lớp Học", bg=AppTheme.PRIMARY, fg=AppTheme.BG_CARD, font=AppTheme.BTN_TEXT, bd=0, command=save).pack(fill=tk.X, pady=20, ipady=12)

    def toggle_class(self, cid, st):
        if st == 0: 
            cls_info = CoreManager.get_query("SELECT CurrentEnrollment FROM COURSE_CLASS WHERE ClassID = ?", (cid,))[0]
            if cls_info['CurrentEnrollment'] > 0:
                ans = messagebox.askyesno("Cảnh báo Nghiêm trọng", f"Lớp {cid} đang có {cls_info['CurrentEnrollment']} SV đăng ký.\nViệc khóa lớp sẽ HỦY TOÀN BỘ đăng ký của sinh viên. Tiếp tục?")
                if not ans: return
                CoreManager.execute_query("DELETE FROM REGISTRATION_FORM WHERE ClassID = ?", (cid,))
                CoreManager.execute_query("UPDATE COURSE_CLASS SET CurrentEnrollment = 0 WHERE ClassID = ?", (cid,))
                messagebox.showinfo("Thông báo", "Đã khóa lớp và hủy các đăng ký liên quan.")
                
        new_st = 1 if st == 0 else 0
        CoreManager.execute_query("UPDATE COURSE_CLASS SET Status = ? WHERE ClassID = ?", (new_st, cid))
        self.view_classes()

    def view_audit(self):
        self.set_subpage("Duyệt Tốt nghiệp")
        apps = CoreManager.get_query("SELECT * FROM GRADUATION_APP")
        if not apps: 
            tk.Label(self.main_content, text="Không có đơn nào", bg=AppTheme.BG_APP, fg=AppTheme.TEXT_MUTED).pack(pady=20)
            return
            
        scroll = self.create_scroll_canvas()
        for a in apps:
            card = tk.Frame(scroll, bg=AppTheme.BG_CARD, padx=15, pady=15, relief=tk.FLAT)
            card.pack(fill=tk.X, pady=6)
            tk.Label(card, text=f"Mã Đơn: {a['AppID']}", font=AppTheme.TITLE_L, bg=AppTheme.BG_CARD, fg=AppTheme.TEXT_MAIN).pack(anchor="w")
            tk.Label(card, text=f"Sinh viên: {a['StudentID']}", font=AppTheme.BODY_M, fg=AppTheme.TEXT_MUTED, bg=AppTheme.BG_CARD).pack(anchor="w", pady=(2,0))
            tk.Label(card, text=f"Trạng thái: {a['Status']}", font=AppTheme.TITLE_S, fg=AppTheme.PRIMARY if "Pending" not in a['Status'] else AppTheme.WARNING, bg=AppTheme.BG_CARD).pack(anchor="w", pady=(0,10))
            
            if a['Status'] == 'Pending':
                btn_frame = tk.Frame(card, bg=AppTheme.BG_CARD)
                btn_frame.pack(fill=tk.X)
                tk.Button(btn_frame, text="Từ chối", font=AppTheme.BTN_TEXT, bg=AppTheme.DANGER, fg=AppTheme.BG_CARD, bd=0, command=lambda appid=a['AppID']: self.reject_app(appid)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5), ipady=5)
                tk.Button(btn_frame, text="Duyệt", font=AppTheme.BTN_TEXT, bg=AppTheme.SUCCESS, fg=AppTheme.BG_CARD, bd=0, command=lambda appid=a['AppID']: self.approve_app(appid)).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5,0), ipady=5)

    def approve_app(self, appid):
        CoreManager.execute_query("UPDATE GRADUATION_APP SET Status = 'Approved' WHERE AppID = ?", (appid,))
        messagebox.showinfo("OK", "Đã duyệt bằng tốt nghiệp!")
        self.view_audit()

    def reject_app(self, appid):
        reason = simpledialog.askstring("Từ chối xét duyệt", "Vui lòng nhập lý do từ chối (VD: Nợ học phí, Thiếu tín chỉ):")
        if reason:
            CoreManager.execute_query("UPDATE GRADUATION_APP SET Status = ? WHERE AppID = ?", (f"Rejected ({reason})", appid))
            messagebox.showinfo("OK", "Đã từ chối đơn tốt nghiệp!")
            self.view_audit()