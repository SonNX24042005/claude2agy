# Claude2AGY 🚀

**Claude2AGY** là công cụ CLI chuyên dụng giúp tự động chuyển đổi các phiên trò chuyện từ **Claude Code (`.jsonl`)** thành các **Session chính thức (Native Sessions)** trên hệ thống **Antigravity CLI (`agy`)**, giữ nguyên ngữ cảnh và hiển thị đầy đủ giao diện câu hỏi - câu trả lời AI trong Terminal.

---

## ✨ Các Tính Năng Nổi Bật

- 🎮 **Interactive Arrow Key Menu:** Tự động phát hiện và hiển thị danh sách các đoạn chat Claude thuộc dự án hiện tại với giao diện điều hướng bằng phím mũi tên `↑` / `↓` và `ENTER`.
- 🔍 **Auto-Discovery:** Tự động quét thư mục `~/.claude/projects/` để tìm các phiên làm việc phù hợp khi không chỉ định tệp.
- ⚡ **Zero-Setup Execution (`./run.sh`):** Cung cấp script chạy trực tiếp ngay khi clone về máy mới mà không bắt buộc phải thực hiện `pip install`.
- 🤖 **Full TUI AI Response Rendering:** Tự động nạp hoàn chỉnh các câu trả lời của AI (`PLANNER_RESPONSE`) để khi mở session bằng `agy`, khung chat AI hiển thị đẹp mắt dưới mỗi câu hỏi.
- 🗄️ **SQLite & Metadata Sync:** Khởi tạo tệp SQLite `conversations/<session-id>.db` và đăng ký session vào `conversation_summaries.db`.

---

## 📂 Cấu Trúc Dự Án

```text
claude2agy/
├── claude2agy/
│   ├── __init__.py       # Khởi tạo package
│   ├── converter.py      # Bộ xử lý bóc tách JSONL & đồng bộ SQLite DB Native
│   ├── menu.py           # Giao diện menu di chuyển bằng phím mũi tên (Curses TUI)
│   └── cli.py            # Entry point xử lý các tham số dòng lệnh
├── run.sh                # Script thực thi nhanh không cần cài đặt
├── setup.py              # Cấu hình cài đặt Python package chuẩn
├── .gitignore            # Loại bỏ các tệp rác, venv và build artifacts
└── README.md             # Hướng dẫn sử dụng chi tiết
```

---

## 🚀 Hướng Dẫn Sử Dụng

### 1️⃣ Cách 1: Chạy trực tiếp (Không cần cài đặt global)
Ngay sau khi clone dự án về máy, di chuyển vào thư mục dự án và chạy `./run.sh`:

```bash
cd scratch/claude2agy

# Mở menu tương tác chọn phiên chat Claude của dự án hiện tại:
./run.sh

# Hoặc chỉ định tệp .jsonl cụ thể:
./run.sh -f /path/to/claude_session.jsonl
```

---

### 2️⃣ Cách 2: Cài đặt lệnh `claude2agy` toàn hệ thống
Nếu muốn sử dụng lệnh `claude2agy` ở bất kỳ thư mục dự án nào:

```bash
cd scratch/claude2agy
pip install -e .
```

Sau khi cài đặt, mở bất kỳ thư mục dự án nào trong terminal và gõ:

```bash
# Mở menu chọn chat của dự án đó:
claude2agy

# Hoặc chuyển đổi tệp chỉ định:
claude2agy --file /path/to/claude_session.jsonl
```

---

## 🎮 Hướng Dẫn Điều Hướng Menu Tương Tác

Khi gõ `claude2agy` hoặc `./run.sh` không truyền tham số, màn hình terminal sẽ hiển thị danh sách các đoạn chat:

```text
🔍 Select a Claude Code session for project [auto-design-ai]:
Use ↑ / ↓ arrow keys to navigate, ENTER to select, 'q' to quit:
---------------------------------------------------------------------------
❯ 2026-07-21 14:21 | Cho nội dung sau """cái e ngâm cứu những hôm vừa r là cái lu...
  2026-07-15 13:37 | Dựa vào các tài liệu md hãy thay thế cho tôi mô hình...
  2026-07-13 16:23 | Viết script train mô hình yolo 26l cho bộ dữ liệu...
```

- **Phím `↑` (Up) / `↓` (Down)** hoặc `k` / `j`: Di chuyển thanh vệt sáng chọn phiên chat.
- **Phím `ENTER`**: Xác nhận chọn phiên làm việc.
- **Phím `q` hoặc `ESC`**: Hủy bỏ.

---

## 📌 Mở Session Sau Khi Chuyển Đổi

Sau khi chuyển đổi thành công, công cụ sẽ in ra câu lệnh `agy` tương ứng. Bạn chỉ cần copy và chạy:

```bash
agy --conversation <GENERATED_SESSION_ID>
```
