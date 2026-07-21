# Claude2AGY & AGY2Claude

Bộ công cụ chuyển đổi hai chiều giữa **Claude Code (`.jsonl`)** và **Antigravity CLI (`agy`)**, hỗ trợ tự động lọc session theo từng dự án (Strict Project Scope).

---

## Giới thiệu

Công cụ giúp chuyển đổi lịch sử hội thoại giữa **Claude Code** và **Antigravity CLI (`agy`)**:
- **Claude Code -> Antigravity (`claude2agy`)**: Chuyển các phiên làm việc từ Claude Code sang Antigravity để tiếp tục đoạn chat.
- **Antigravity -> Claude Code (`agy2claude`)**: Xuất phiên làm việc từ Antigravity về định dạng Claude Code `.jsonl`.
- **Lọc theo dự án**: Tự động nhận diện thư mục hiện tại để chỉ hiển thị các phiên chat thuộc đúng dự án đó.

---

## Cài đặt nhanh bằng 1 câu lệnh (One-Line Install)

### 1. Trên Linux, macOS, WSL hoặc Git Bash (Windows)

Mở Terminal và dán câu lệnh sau:

```bash
curl -fsSL https://raw.githubusercontent.com/SonNX24042005/claude2agy/main/install.sh | bash
```

---

### 2. Trên Windows (PowerShell)

Mở PowerShell và dán câu lệnh sau:

```powershell
iwr -useb https://raw.githubusercontent.com/SonNX24042005/claude2agy/main/install.ps1 | iex
```

*Lưu ý: Sau khi cài đặt xong, hãy khởi động lại Terminal để hệ thống nhận 2 lệnh `claude2agy` và `agy2claude`.*

---

## Hướng dẫn sử dụng

Sau khi cài đặt, bạn di chuyển vào **thư mục dự án bất kỳ** và chạy lệnh:

### 1. Chuyển từ Claude Code sang Antigravity (`claude2agy`)

```bash
cd /path/to/your-project
claude2agy
```
1. Danh sách phiên chat Claude Code thuộc dự án sẽ xuất hiện. Dùng phím `↑` / `↓` chọn và nhấn `Enter`.
2. Sao chép câu lệnh được tạo ra và chạy để tiếp tục hội thoại:
   ```bash
   agy --conversation <SESSION_ID>
   ```

---

### 2. Chuyển từ Antigravity sang Claude Code (`agy2claude`)

```bash
cd /path/to/your-project
agy2claude
```
1. Chọn phiên chat Antigravity muốn chuyển đổi từ menu.
2. File `.jsonl` sẽ tự động xuất vào thư mục của Claude Code (`~/.claude/projects/`).

---

## Cài đặt thủ công (Manual Installation)

Nếu không dùng 1-line install, bạn có thể clone dự án thủ công:

```bash
git clone https://github.com/SonNX24042005/claude2agy.git
cd claude2agy

# Cách A: Dùng ngay bằng script
chmod +x run.sh
./run.sh                  # Claude Code -> Antigravity
./run.sh --reverse        # Antigravity -> Claude Code

# Cách B: Cài đặt lệnh vào hệ thống bằng pip
pip install -e .
```

---

## Các tùy chọn dòng lệnh (Command-line Arguments)

| Tham số | Ý nghĩa | Ví dụ |
| :--- | :--- | :--- |
| `-f`, `--file` | Chỉ định đường dẫn file `.jsonl` của Claude Code | `claude2agy -f /path/to/session.jsonl` |
| `-s`, `--session` | Chỉ định Antigravity Session ID | `agy2claude -s 2c3ed564-11bb-435c-b8f5` |
| `-c`, `--cwd` | Chỉ định đường dẫn dự án đích | `claude2agy -c /path/to/target/project` |

---

## Xử lý sự cố thường gặp

### 1. Lỗi "No Claude session logs (.jsonl) found..."
- **Nguyên nhân**: Thư mục hiện tại chưa từng được sử dụng với Claude Code hoặc chưa có file log trong `~/.claude/projects/`.
- **Khắc phục**: Di chuyển (`cd`) chính xác vào thư mục dự án mà bạn đã chạy Claude Code trước đó.

### 2. Lỗi "command not found: claude2agy" sau khi cài đặt
- **Khắc phục**: 
  - Khởi động lại Terminal.
  - Hoặc thêm `export PATH="$HOME/.local/bin:$PATH"` vào file `~/.bashrc` (hoặc `~/.zshrc`).



