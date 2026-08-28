"""MCP Server có Authentication — Bảo mật cho E-Commerce Order System.

Server chạy qua HTTP (Streamable HTTP), kèm xác thực Bearer Token.
Chỉ các request mang token hợp lệ mới được phép khám phá và gọi tool tra cứu đơn hàng.

Luồng hoạt động:
  Client gửi HTTP Request kèm header: Authorization: Bearer <token>
    → TokenVerifier kiểm tra token
    → Hợp lệ: Trả về kết quả từ DB orders.json
    → Sai / Thiếu: Trả về mã lỗi 401/403

Cách chạy:
    python server_auth.py
    (Lắng nghe tại http://0.0.0.0:8080/mcp)
"""

from __future__ import annotations
import os
import json
from pathlib import Path
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

# Token Store: Cấu hình danh sách token hợp lệ
VALID_TOKENS: dict[str, str] = {
    os.environ.get("ORDER_AUTH_TOKEN", "order-secret-token-2026"): "cskh-service",
    "admin-super-key-999": "admin-portal",
}

class OrderTokenVerifier(TokenVerifier):
    """Kiểm tra bearer token dựa trên danh sách hợp lệ."""
    async def verify_token(self, token: str) -> AccessToken | None:
        client_id = VALID_TOKENS.get(token)
        if client_id is None:
            return None
        return AccessToken(token=token, client_id=client_id, scopes=["orders:read", "orders:manage"])

# Khởi tạo MCP Server với Auth
mcp = MCPServer(
    "order-auth-server",
    auth=AuthSettings(
        issuer_url="http://localhost:8080",
        resource_server_url="http://localhost:8080",
    ),
    token_verifier=OrderTokenVerifier(),
)

DATA_FILE = Path(__file__).parent / "data" / "orders.json"

def load_orders() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@mcp.tool()
def get_order_details(order_id: str) -> str:
    """Tra cứu chi tiết đơn hàng (Yêu cầu xác thực Bearer Token)."""
    orders = load_orders()
    target_id = order_id.strip().upper()
    for order in orders:
        if order["id"].upper() == target_id:
            return json.dumps(order, ensure_ascii=False, indent=2)
    return f"❌ Không tìm thấy đơn hàng {order_id}"

@mcp.tool()
def search_orders_by_status(status: str, limit: int = 5) -> str:
    """Tìm kiếm đơn hàng theo trạng thái (Yêu cầu xác thực Bearer Token)."""
    orders = load_orders()
    target_status = status.strip().lower()
    results = [o for o in orders if o.get("status", "").lower() == target_status][:limit]
    return json.dumps({"status": status, "orders": results}, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🔒 Đang khởi động Secure Order MCP Server trên http://0.0.0.0:{port}/mcp")
    print(f"🔑 Token kiểm thử: 'order-secret-token-2026'")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
