# Test Automation Guide - UTH Portal Mobile

## 1. Công cụ và framework

Project là ứng dụng Python desktop/Tkinter dùng SQLite local, không có backend API. Bộ automation hiện tại chạy theo hướng UI-first: mỗi Test Case mở cửa sổ Tkinter thật, thao tác trên màn hình/helper UI, sau đó có thể đọc SQLite tạm để assert kết quả sau thao tác.

- Python standard library.
- Custom runner: `tests/runner.py`.
- Test case folder: `tests/testcases/`.
- Registry: `tests/testcases/test-case-registry.json`.
- Test case document: `tests/testcases/TEST_CASES.md`.
- Test database helper: `tests/helpers/database_helper.py`.
- UI app helper: `tests/helpers/ui_helper.py`.
- JSON seed data: `tests/fixtures/seed_data.json`.
- Seed importer: `tests/fixtures/import_seed_data.py`.
- Test data factory: `tests/fixtures/test_data_factory.py`.

Không cần package bên thứ ba để chạy test.

## 2. Cài dependency

Nếu chưa có virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`requirements.txt` hiện không có dependency ngoài vì app và test runner chỉ dùng standard library.

## 3. Cấu hình `.env.test`

File mẫu đã tạo:

```text
.env.test.example
```

Nội dung:

```env
TEST_ENVIRONMENT=local
TEST_DATABASE_FILE=uth_portal_final.db
```

Nếu cần, tạo file `.env.test` riêng cho máy local. Test runner sẽ đọc `.env.test` trước khi kiểm tra môi trường. Không đưa secret vào `.env.test` và không commit file này.

## 4. Khởi động hệ thống test

Không cần khởi động server. Mỗi test tự tạo một thư mục tạm, chạy `initialize_database()` để sinh SQLite database riêng, sau đó cleanup khi test kết thúc.

Seed data phục vụ testcase được đọc từ:

```text
tests/fixtures/seed_data.json
```

Importer tự động nạp seed vào database tạm khi test dùng `DatabaseHelper` hoặc `UiAppHelper`. Nếu cần import seed vào database runtime ở root project:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -validate
.\.venv\Scripts\python.exe .\tests\fixtures\import_seed_data.py --db .\uth_portal_final.db
```

Hoặc dùng script wrapper có sẵn:

```powershell
.\scripts\seed-automation-data.bat --with-scenarios
```

## 5. Chạy toàn bộ test

PowerShell trên Windows nên chạy qua `-ExecutionPolicy Bypass` để tránh lỗi policy chặn script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -all
```

Lệnh này sẽ mở UI Tkinter cho từng test case.

Nếu muốn xem UI thao tác chậm hơn và có log tiến trình:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -all -delay 1 -stepDelay 1
```

Runner sẽ in log dạng:

```text
[PROCESSING] TC001 - Open App
[CASE] TC001 - Positive
[PROCESSING] TC001 - STEP 1 - 1. Open the application UI.
[INPUT] TC001 - App: `MainApp`
[EXPECTED] TC001 - Application opens successfully and local database schema is initialized.
```

Trong đó `-delay` là thời gian chờ trước mỗi Test Case, còn `-stepDelay` là thời gian chờ giữa các thao tác/cập nhật UI trong từng Test Case.

Hoặc gọi trực tiếp runner:

```powershell
.\.venv\Scripts\python.exe -m tests.runner --all
```

## 6. Chạy một Test Case theo ID

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -id TC003
```

Hoặc:

```powershell
.\.venv\Scripts\python.exe -m tests.runner --id TC003
```

## 7. Chạy theo Function, Tag hoặc Type

Theo Function:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -function "Login"
```

Theo Tag:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -tag auth
```

Theo Type:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -type UI
```

Chạy riêng nhóm UI automation để mở cửa sổ Tkinter và tự thao tác:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -tag ui
```

## 8. Validate đồng bộ tài liệu và automation

Lệnh validate kiểm tra:

- Test Case có trong `tests/testcases/TEST_CASES.md` nhưng thiếu registry.
- Registry có ID nhưng thiếu trong tài liệu.
- ID bị trùng.
- Test Case thiếu Function hoặc Expected Result.
- Test Case thiếu Label hoặc Label trong Markdown lệch với tag registry.
- Test Case marked automated nhưng không load được implementation.

Chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -validate
```

Nếu có lỗi mapping, command trả về exit code khác `0`.

## 9. Xem báo cáo

Sau mỗi lần chạy test, runner tạo:

```text
test-results/
|-- latest-report.md
|-- latest-report.json
`-- junit-results.xml
```

Mở file sau để xem báo cáo Markdown:

```text
test-results/latest-report.md
```

## 10. Thêm Test Case mới

1. Thêm dòng mới vào `tests/testcases/TEST_CASES.md` với ID tiếp theo, ví dụ `TC030`.
2. Thêm function test vào file phù hợp, thường là `tests/ui/test_portal_ui.py` nếu test thao tác UI.
3. Gắn decorator:

```python
@testcase("TC030")
def tc030_new_behavior(repo_root: Path) -> None:
    ...
```

4. Thêm entry tương ứng vào `tests/testcases/test-case-registry.json`.
5. Chạy validate:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -validate
```

6. Chạy test mới:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 -id TC030
```

## 11. Cập nhật registry

Mỗi entry registry cần có:

```json
{
  "id": "TC001",
  "function": "Login",
  "type": "UI",
  "tags": ["ui", "auth", "positive"],
  "automated": true,
  "testTarget": "tests.ui.test_portal_ui.tc001_example"
}
```

`testTarget` phải là đường dẫn import Python load được. Runner dùng registry để lọc theo `--id`, `--function`, `--tag`, `--type` và để validate đồng bộ.

## 12. Xử lý lỗi thường gặp

- `No test cases matched the selected filters`: ID, function, tag hoặc type không tồn tại trong registry.
- `cannot load testTarget`: sai module/function trong `tests/testcases/test-case-registry.json`.
- `running scripts is disabled on this system`: dùng lệnh `powershell -ExecutionPolicy Bypass -File .\scripts\run-tests.ps1 ...`.
- Lỗi SQLite `no such table`: test chưa mở app qua `UiAppHelper` hoặc database tạm chưa được khởi tạo.
- Lỗi import `core`: cần chạy command từ root project hoặc dùng `scripts/run-tests.ps1`.
- Test FAIL nhưng app vẫn chạy: xem `test-results/latest-report.md` để biết assertion nào sai.

## 13. Giới hạn hiện tại

- UI automation Tkinter đã được bổ sung cho các luồng có thể thao tác ổn định qua helper nội bộ. Khi chạy `-type UI` hoặc `-tag ui`, cửa sổ app thật sẽ được mở, test sẽ nhập/bấm trên widget Tkinter và đóng app sau mỗi test.
- UI automation cần chạy trên môi trường có desktop session. Nếu chạy trên headless CI không có display, các test UI có thể lỗi do Tkinter không tạo được window.
- Không có API tests vì project không expose endpoint.
- Chức năng nhập điểm hiện chỉ hiển thị thông báo, nên automation assert thông báo UI thay vì assert lưu điểm vào database.
