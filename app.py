# --- FILE: app.py ---
from flask import Flask, request, jsonify
from config import Config
from models import db, Account, Student, CourseClass

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# ==========================================
# LỚP QUẢN LÝ (SERVICE/MANAGER CLASSES)
# ==========================================
class AuthenticationManager:
    """Lớp nghiệp vụ xử lý Đăng nhập"""
    @staticmethod
    def process_login(account_id: str, password_input: str) -> dict:
        user_account = Account.query.filter_by(AccountID=account_id).first()
        
        # Gọi method verify_password của đối tượng Account (Chuẩn OOP)
        if user_account and user_account.verify_password(password_input):
            return {"status": "success", "role": user_account.Role, "owner_id": user_account.OwnerID}
        return {"status": "error", "message": "Sai tài khoản hoặc mật khẩu"}


# ==========================================
# CÁC CỔNG API (ROUTES)
# ==========================================

# API 1: Đăng nhập (Use Case: Login to System)
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    # Giao việc cho Lớp Quản lý xử lý
    result = AuthenticationManager.process_login(data.get('username'), data.get('password'))
    
    if result["status"] == "success":
        return jsonify(result), 200
    return jsonify(result), 401


# API 2: Lấy thông tin Sinh viên (Use Case: View Information)
@app.route('/api/student/<student_id>', methods=['GET'])
def api_get_student(student_id):
    student_obj = Student.query.get(student_id)
    
    if student_obj:
        # Gọi method to_dict() của đối tượng Student
        return jsonify({"status": "success", "data": student_obj.to_dict()}), 200
    return jsonify({"status": "error", "message": "Không tìm thấy sinh viên"}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)