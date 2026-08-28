# My MCP Server — E-Commerce Order Management System

Dự án tích hợp MCP Server cá nhân hóa phục vụ tra cứu, phân loại đơn hàng và tính toán doanh thu tự động cho hệ thống Thương mại điện tử.

---

## 📌 Bước 1 — Use Case (Công việc thực tế)

- **Công việc hiện tại:** Nhân viên Chăm sóc Khách hàng (CSKH) & Quản trị kho hàng ngày phải liên tục tra cứu thông tin đơn hàng, kiểm tra tiến độ giao hàng cho khách khiếu nại, và thống kê doanh thu/đơn hàng cần xử lý.
- **Tôi đang làm thủ công như thế nào:** Khi có yêu cầu kiểm tra đơn hàng, nhân viên phải mở file Excel / giao diện quản trị, dùng `Ctrl + F` gõ mã đơn, đọc từng trường dữ liệu, tính toán tiền thanh toán sau giảm giá, rồi sao chép mã vận đơn lên trang tra cứu chuyển phát nhanh.
- **Input:** Mã đơn hàng (ví dụ: `ORD-101`, `ORD-102`), trạng thái đơn hàng (`pending`, `shipping`, `delivered`, `cancelled`).
- **Output:** Thông tin chi tiết đơn hàng (khách hàng, sản phẩm, địa chỉ, tổng tiền, mã vận đơn) hoặc danh sách lọc theo trạng thái kèm báo cáo doanh thu.

---

## 📌 Bước 2 — Thiết kế Tools

Hệ thống được thiết kế với các MCP Tools đọc dữ liệu thực tế từ cơ sở dữ liệu `data/orders.json` (không hard-code):

| Tool | Input | Output | Mô tả |
| :--- | :--- | :--- | :--- |
| `get_order_details` | `order_id: str` | `str` (JSON string) | Tra cứu chi tiết đơn hàng theo mã đơn (khách hàng, sản phẩm, địa chỉ, trạng thái). |
| `search_orders_by_status` | `status: str`, `limit: int = 5` | `str` (JSON string) | Tìm kiếm và lọc danh sách các đơn hàng theo trạng thái (`pending`, `shipping`, `delivered`, `cancelled`). |
| `calculate_revenue` | `status: str = "delivered"` | `str` (JSON string) | Thống kê số lượng đơn và tổng doanh thu (VNĐ) tương ứng với trạng thái đã chọn. |

---

## 📌 Bước 3 — Cấu trúc & Hướng dẫn chạy MCP Server

### Cấu trúc thư mục
```
my-mcp-server/
├── data/
│   └── orders.json            # Cơ sở dữ liệu mẫu thực tế
├── server.py                  # MCP Server cơ bản (stdio)
├── server_auth.py             # MCP Server có Authentication (HTTP)
├── server_versioned.py        # MCP Server có Versioning (v1/v2 + server://info)
├── test_client.py             # Script kiểm thử tự động
├── requirements.txt           # Thư viện phụ thuộc
└── README.md                  # Tài liệu hướng dẫn
```

### Cài đặt môi trường
```bash
pip install -r requirements.txt
```

### Chạy MCP Server (stdio mode)
```bash
python server.py
```

### Chạy kiểm thử tự động toàn diện
```bash
python test_client.py
```

---

## 📌 Bước 4 — Đăng ký MCP Server vào Claude Code / AI Assistant

### Cấu hình `mcp_config.json` hoặc cấu hình Claude Desktop:
```json
{
  "mcpServers": {
    "order-management": {
      "command": "python",
      "args": [
        "c:/23020382_Ngô Nguyễn Khải Hưng/Day26-MCP-Tools-Integration-2A202601216/my-mcp-server/server.py"
      ]
    }
  }
}
```

### Luồng tương tác bằng ngôn ngữ tự nhiên:

```
User: "Kiểm tra giúp tôi đơn hàng ORD-101 đang ở đâu và tổng tiền bao nhiêu?"
   │
   ▼
Claude Code / AI Assistant (Phân tích prompt -> Chọn tool get_order_details)
   │
   │ args: {"order_id": "ORD-101"}
   ▼
MCP Server (server.py thực thi đọc file data/orders.json)
   │
   │ Trả về JSON: {"id": "ORD-101", "status": "shipping", "address": "Hà Nội", ...}
   ▼
AI Assistant tổng hợp:
"Đơn hàng ORD-101 của khách hàng Nguyễn Văn An đang ở trạng thái 'shipping' (đang giao đến Cầu Giấy, Hà Nội).
Tổng giá trị đơn hàng là 450.000 VNĐ (đã áp dụng mã giảm giá 50.000 VNĐ). Mã vận đơn: VNPOST-ORD101-VN."
```

---

## 📌 Bước 5 — Authentication (Bảo mật với Streamable HTTP & TokenVerifier)

Khi triển khai trên mạng nội bộ hoặc Production, server chuyển sang giao thức **Streamable HTTP** kèm xác thực **Bearer Token**.

### Sơ đồ xác thực:
```
MCP Client ──[Authorization: Bearer <token>]──► TokenVerifier (server_auth.py)
                                                        │
                                    ┌───────────────────┴───────────────────┐
                                    ▼                                       ▼
                             Token Hợp Lệ                         Token Sai / Thiếu
                                    │                                       │
                                    ▼                                       ▼
                            Trả về kết quả (200)                    Từ chối (401 / 403)
```

### Cách chạy Server có xác thực:
```bash
python server_auth.py
# Server chạy tại http://0.0.0.0:8080/mcp
```

### Kết quả kiểm thử bảo mật:
1. **Request không có token:** Server phản hồi `401 Unauthorized`.
2. **Request mang token sai (`Bearer invalid-token`):** Server phản hồi `401 Unauthorized` / `403 Forbidden`.
3. **Request mang token đúng (`Bearer order-secret-token-2026`):** Xác thực thành công và thực thi tool bình thường.

---

## 📌 Bước 6 — Versioning & Backward Compatibility

Nhằm nâng cấp định dạng dữ liệu trả về mà không làm hỏng (break) các ứng dụng Client cũ đang sử dụng, hệ thống áp dụng chiến lược **Versioning song song**:

### 1. So sánh Tool v1 và v2:
* **Tool v1 (`get_order_details`):** Trả về chuỗi JSON rút gọn gồm các trường cơ bản (`id`, `status`, `customer_name`, `total_amount`) cho các client thế hệ cũ.
* **Tool v2 (`get_order_details_v2`):** Trả về đầy đủ thông tin mở rộng (`items`, `tracking_number`, `phone`, `discount`, `final_amount`, `updated_at`, `queried_at`), kèm các tham số tùy chọn có giá trị mặc định (`include_tracking=True`, `include_items=True`).

### 2. Resource `server://info`:
Server cung cấp resource metadata `server://info` giúp Client tự động kiểm tra năng lực và lộ trình nâng cấp:
```json
{
  "name": "order-versioned-server",
  "version": "2.0.0",
  "tools": {
    "get_order_details": {
      "version": "1.0.0",
      "status": "deprecated",
      "replacement": "get_order_details_v2"
    },
    "get_order_details_v2": {
      "version": "2.0.0",
      "status": "active"
    }
  },
  "migration_guide": "Khuyến nghị chuyển sang dùng 'get_order_details_v2'..."
}
```

### 3. Cơ chế Fallback thông minh của Client:
```python
# Client đọc server://info để quyết định tool:
if "get_order_details_v2" in available_tools:
    result = session.call_tool("get_order_details_v2", {"order_id": "ORD-101", "include_tracking": True})
else:
    result = session.call_tool("get_order_details", {"order_id": "ORD-101"})
```

---

## 📌 Bước 7 — Hướng dẫn kiểm tra và Nộp bài (Git Push)

Thực hiện các lệnh sau trong terminal để lưu trữ và đẩy toàn bộ bài làm lên GitHub:

```bash
git add .
git commit -m "feat: complete my-mcp-server with use-case, auth, versioning, and tests"
git push origin main
```
