"""MCP Server có Versioning — Quản lý phiên bản và tương thích ngược (Backward Compatibility).

Kỹ thuật:
  1. Hỗ trợ song song cả v1 (get_order_details) và v2 (get_order_details_v2).
  2. Tham số mở rộng có giá trị mặc định (default parameters).
  3. Cung cấp Resource server://info để client kiểm tra capability & deprecation notices.
"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from mcp.server.mcpserver import MCPServer

SERVER_VERSION = "2.0.0"

mcp = MCPServer(
    "order-versioned-server",
    instructions=f"Order MCP Server v{SERVER_VERSION}. Hỗ trợ get_order_details (v1 legacy) và get_order_details_v2 (rich details & tracking).",
)

DATA_FILE = Path(__file__).parent / "data" / "orders.json"

def load_orders() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ── Resource: server://info (Cung cấp Metadata cho Client) ───────────────
@mcp.resource("server://info")
def server_info() -> str:
    """Metadata phiên bản server, danh sách tools hỗ trợ và hướng dẫn nâng cấp."""
    return json.dumps(
        {
            "name": "order-versioned-server",
            "version": SERVER_VERSION,
            "tools": {
                "get_order_details": {
                    "version": "1.0.0",
                    "status": "deprecated",
                    "replacement": "get_order_details_v2",
                    "description": "Chỉ trả về thông tin trạng thái cơ bản"
                },
                "get_order_details_v2": {
                    "version": "2.0.0",
                    "status": "active",
                    "description": "Trả về chi tiết sản phẩm, tracking number, và timeline cập nhật"
                }
            },
            "migration_guide": "Khuyến nghị chuyển sang dùng 'get_order_details_v2' với các tham số mở rộng 'include_tracking' và 'include_items'."
        },
        ensure_ascii=False,
        indent=2
    )

# ── Tool v1.0.0 (Giữ nguyên tương thích ngược cho Client cũ) ─────────────
@mcp.tool()
def get_order_details(order_id: str) -> str:
    """[v1.0.0] Tra cứu trạng thái đơn hàng cơ bản (Legacy client)."""
    orders = load_orders()
    target_id = order_id.strip().upper()
    for o in orders:
        if o["id"].upper() == target_id:
            # Client cũ chỉ nhận format rút gọn: id, status, customer_name
            return json.dumps({
                "api_version": "1.0",
                "id": o["id"],
                "customer_name": o["customer_name"],
                "status": o["status"],
                "total_amount": o["total_amount"]
            }, ensure_ascii=False)
            
    return f"Không tìm thấy đơn {order_id}"

# ── Tool v2.0.0 (Phiên bản mới với đầy đủ tính năng mở rộng) ─────────────
@mcp.tool()
def get_order_details_v2(
    order_id: str,
    include_tracking: bool = True,
    include_items: bool = True
) -> str:
    """[v2.0.0] Tra cứu thông tin đơn hàng chi tiết, lịch sử cập nhật và mã vận đơn.

    Args:
        order_id: Mã đơn hàng (ví dụ: 'ORD-101')
        include_tracking: Có bao gồm mã vận đơn và thông tin giao hàng không (mặc định: True)
        include_items: Có bao gồm danh sách chi tiết các mặt hàng không (mặc định: True)
    """
    orders = load_orders()
    target_id = order_id.strip().upper()
    for o in orders:
        if o["id"].upper() == target_id:
            result = {
                "api_version": "2.0",
                "id": o["id"],
                "customer_name": o["customer_name"],
                "phone": o["phone"],
                "status": o["status"],
                "address": o["address"],
                "payment_method": o["payment_method"],
                "total_amount": o["total_amount"],
                "discount": o["discount"],
                "final_amount": o["total_amount"] - o["discount"],
                "created_at": o["created_at"],
                "updated_at": o["updated_at"],
                "queried_at": datetime.now(timezone.utc).isoformat()
            }
            if include_tracking:
                result["tracking_number"] = o.get("tracking_number") or "Chưa có mã vận đơn"
            if include_items:
                result["items"] = o.get("items", [])
                
            return json.dumps(result, ensure_ascii=False, indent=2)
            
    return json.dumps({"api_version": "2.0", "error": f"Không tìm thấy đơn {order_id}"}, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()
