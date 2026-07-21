# Claude2AGY & AGY2Claude

Bộ công cụ chuyển đổi hai chiều giữa **Claude Code (`.jsonl`)** và **Antigravity CLI (`agy`)**, hỗ trợ tự động lọc session theo từng dự án (Strict Project Scope).

---

## Giới thiệu

Công cụ giúp chuyển đổi lịch sử hội thoại giữa **Claude Code** và **Antigravity CLI (`agy`)**:
- **Claude Code -> Antigravity (`claude2agy`)**: Chuyển các phiên làm việc từ Claude Code sang Antigravity để tiếp tục đoạn chat.
- **Antigravity -> Claude Code (`agy2claude`)**: Xuất phiên làm việc từ Antigravity về định dạng Claude Code `.jsonl`.
- **Lọc theo dự án**: Tự động nhận diện thư mục hiện tại để chỉ hiển thị các phiên chat thuộc đúng dự án đó.

---

## Yêu cầu hệ thống

- **Hệ điều hành**: Linux, macOS, hoặc Windows (WSL/Git Bash).
- **Python**: Python 3.8 trở lên (kiểm tra bằng lệnh `python3 --version`).
- Chỉ sử dụng thư viện chuẩn của Python, không cần cài đặt thêm thư viện bên ngoài.

---

## Hướng dẫn sử dụng cho người mới

### Bước 1: Clone dự án về máy

Mở Terminal và chạy các lệnh:

```bash
# Clone repository từ GitHub
git clone https://github.com/<username>/claude2agy.git

# Di chuyển vào thư mục dự án
cd claude2agy
```

---

### Bước 2: Lựa chọn cách chạy công cụ

Bạn có thể chọn một trong hai cách dưới đây:

#### Cách 1: Sử dụng ngay bằng `./run.sh` (Không cần cài đặt)

Phù hợp nếu bạn muốn sử dụng ngay sau khi clone mà không thay đổi môi trường hệ thống.

```bash
# Cấp quyền thực thi cho script (chỉ làm lần đầu)
chmod +x run.sh

# Chuyển từ Claude Code sang Antigravity:
./run.sh

# Chuyển ngược từ Antigravity sang Claude Code:
./run.sh --reverse
```

#### Cách 2: Cài đặt lệnh vào hệ thống bằng `pip`

Phù hợp khi dùng thường xuyên. Sau khi cài đặt, bạn có thể gọi lệnh từ bất kỳ thư mục dự án nào.

```bash
pip install -e .
```

Sau khi cài đặt xong, di chuyển tới thư mục dự án bất kỳ và gõ:
```bash
claude2agy     # Chuyển từ Claude Code -> Antigravity
agy2claude     # Chuyển từ Antigravity -> Claude Code
```

---

## Chi tiết các thao tác

### 1. Chuyển từ Claude Code sang Antigravity (`claude2agy`)

1. Di chuyển vào thư mục dự án của bạn (ví dụ: `cd ~/projects/my-app`).
2. Chạy lệnh `claude2agy` (hoặc `./run.sh`).
3. Dùng phím mũi tên `↑` / `↓` để chọn phiên chat và nhấn `Enter`.
4. Sao chép câu lệnh được tạo ra và chạy để tiếp tục hội thoại:
   ```bash
   agy --conversation <SESSION_ID>
   ```

---

### 2. Chuyển từ Antigravity sang Claude Code (`agy2claude`)

1. Di chuyển vào thư mục dự án của bạn.
2. Chạy lệnh `agy2claude` (hoặc `./run.sh --reverse`).
3. Chọn phiên chat Antigravity muốn chuyển đổi từ danh sách.
4. File `.jsonl` sẽ tự động được xuất vào thư mục lưu trữ của Claude Code (`~/.claude/projects/`).

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

### 2. Lỗi "Permission denied" khi chạy `./run.sh`
- **Khắc phục**: Chạy `chmod +x run.sh` để cấp quyền thực thi.

### 3. Không tìm thấy lệnh `claude2agy` sau khi `pip install`
- **Nguyên nhân**: Thư mục chứa file thực thi của pip chưa có trong biến môi trường `PATH`.
- **Khắc phục**: Thêm `export PATH="$HOME/.local/bin:$PATH"` vào file `~/.bashrc` (hoặc `~/.zshrc`), hoặc sử dụng `./run.sh`.


