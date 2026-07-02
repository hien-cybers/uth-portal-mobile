# --- FILE: models.py ---
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 1. CLASS ACCOUNT (Đóng gói - Encapsulation)
class Account(db.Model):
    __tablename__ = 'ACCOUNT'
    AccountID = db.Column(db.String(50), primary_key=True)
    OwnerID = db.Column(db.String(20), nullable=False)
    Password = db.Column(db.String(255), nullable=False) # Thuộc tính cần bảo mật
    Role = db.Column(db.String(20), nullable=False)

    # Method đóng gói: Không cho bên ngoài lấy password, chỉ cho kiểm tra đúng sai
    def verify_password(self, password_input: str) -> bool:
        return self.Password == password_input

# 2. CLASS STUDENT
class Student(db.Model):
    __tablename__ = 'STUDENT'
    StudentID = db.Column(db.String(20), primary_key=True)
    CurriculumID = db.Column(db.String(20))
    Fullname = db.Column(db.String(100))
    
    # Method xử lý nghiệp vụ của Sinh viên
    def to_dict(self) -> dict:
        return {
            "StudentID": self.StudentID,
            "Fullname": self.Fullname,
            "CurriculumID": self.CurriculumID
        }

# 3. CLASS COURSE_CLASS (Lớp học phần)
class CourseClass(db.Model):
    __tablename__ = 'COURSE_CLASS'
    ClassID = db.Column(db.String(20), primary_key=True)
    SubjectID = db.Column(db.String(20))
    MaxCapacity = db.Column(db.Integer)
    CurrentEnrollment = db.Column(db.Integer, default=0)
    Status = db.Column(db.Integer, default=0) # 0: Mở, 1: Khóa

    # Method kiểm tra lớp còn chỗ không
    def is_available(self) -> bool:
        return self.Status == 0 and self.CurrentEnrollment < self.MaxCapacity