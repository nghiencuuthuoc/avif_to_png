# AVIF to PNG Converter — Tkinter GUI hỗ trợ kéo-thả thư mục

Đây là ứng dụng desktop Python dùng Tkinter để chuyển file ảnh `.avif` sang `.png`.

Phiên bản này hỗ trợ:
- chọn thư mục bằng nút **Browse**
- **kéo-thả thư mục input/output**
- quét thư mục con
- giữ nguyên cấu trúc thư mục
- ghi đè hoặc bỏ qua file PNG đã tồn tại
- thanh tiến trình
- bảng log kết quả
- chạy nền bằng thread để GUI không bị đơ

## Tính năng

- Chuyển toàn bộ file `.avif` trong thư mục input sang `.png`
- Kéo-thả **thư mục input**
- Kéo-thả **thư mục output**
- Tùy chọn quét cả thư mục con
- Tùy chọn giữ nguyên cấu trúc thư mục nguồn trong thư mục đích
- Tùy chọn ghi đè file PNG đã có
- Bảng theo dõi trạng thái chuyển đổi
- Mở nhanh thư mục output từ ứng dụng

## Yêu cầu

- Python 3.10+
- Tkinter
- `pillow`
- `pillow-avif-plugin`
- `tkinterdnd2`

## Cài đặt

```bash
pip install -r requirements.txt
```

Hoặc cài thủ công:

```bash
pip install pillow pillow-avif-plugin tkinterdnd2
```

## Chạy chương trình

```bash
python avif_to_png_tk_gui.py
```

## Cách dùng

1. Mở ứng dụng.
2. Chọn thư mục input bằng **Browse...** hoặc kéo-thả vào vùng **Drop INPUT folder here**.
3. Chọn thư mục output bằng **Browse...** hoặc kéo-thả vào vùng **Drop OUTPUT folder here**.
4. Chọn các tùy chọn:
   - **Scan subfolders**
   - **Overwrite existing PNG**
   - **Preserve folder structure**
5. Nhấn **Start Conversion**.
6. Xem kết quả trong bảng log.

## Ghi chú

- Nếu bạn kéo-thả một file thay vì thư mục, ứng dụng sẽ tự lấy thư mục cha của file đó.
- Nếu chưa nhập output folder, ứng dụng sẽ tự tạo thư mục `png_output` bên trong input folder.
- Hỗ trợ AVIF được cung cấp qua `pillow-avif-plugin`.
- Hỗ trợ kéo-thả được cung cấp qua `tkinterdnd2`.

## Cấu trúc dự án

```text
avif_to_png_tk_gui/
├── avif_to_png_tk_gui.py
├── README_EN.md
├── README_VI.md
└── requirements.txt
```

## License

Bạn có thể tự thêm license phù hợp trước khi đăng GitHub.
