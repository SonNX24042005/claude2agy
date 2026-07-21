# Claude2AGY / AGY2Claude 🔄

**Claude2AGY / AGY2Claude** là bộ công cụ CLI chuyển đổi hai chiều (Bi-directional Converter) giữa **Claude Code (`.jsonl`)** và **Antigravity CLI (`agy`)**, với cơ chế **lọc nghiêm ngặt độc quyền theo từng dự án (Strict Project Isolation)**.

---

## ✨ Các Tính Năng Nổi Bật

- 🔒 **Lọc nghiêm ngặt theo dự án hiện tại (Strict Project Scope):**
  - Khi đứng ở dự án A (`claude2agy` hoặc `agy2claude`), menu chỉ hiển thị duy nhất các cuộc hội thoại thuộc về dự án A.
  - Tuyệt đối không hiển thị hay trộn lẫn các session thuộc về dự án B hay dự án khác.
- 🔄 **Chuyển đổi 2 chiều linh hoạt:**
  - **Chiều thuận (`claude2agy`):** Chuyển đổi phiên chat Claude Code (`.jsonl`) $\rightarrow$ Antigravity Native Session (`agy`).
  - **Chiều ngược (`agy2claude`):** Chuyển đổi Antigravity Session $\rightarrow$ Claude Code JSONL (`~/.claude/projects/`).
- 🎮 **Arrow Key Navigation Menu:** Giao diện điều hướng chọn session bằng phím mũi tên `↑` / `↓` và `ENTER`.
- ⚡ **Zero-Setup Execution (`./run.sh`):** Thực thi trực tiếp khi clone về máy mới mà không bắt buộc `pip install`.

---

## 🚀 Hướng Dẫn Sử Dụng

### 1️⃣ Chuyển đổi từ Claude Code sang Antigravity (`claude2agy`)
Đứng tại thư mục dự án bất kỳ và gõ:
```bash
claude2agy
```
Menu tương tác sẽ chỉ liệt kê các đoạn chat Claude Code của đúng dự án đó!

---

### 2️⃣ Chuyển đổi ngược từ Antigravity sang Claude Code (`agy2claude`)
Đứng tại thư mục dự án bất kỳ và gõ:
```bash
agy2claude
```
Menu tương tác sẽ chỉ liệt kê các Antigravity Session thuộc về đúng dự án đó để xuất ra tệp Claude JSONL!
