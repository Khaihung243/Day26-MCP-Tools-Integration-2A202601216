from mcp.server.mcpserver import MCPServer
import json
from pathlib import Path

# Khởi tạo MCP Server chuẩn
mcp = MCPServer("order-management-server")

DATA_FILE = Path(__file__).parent / "data" / "orders.json"

def load_orders() -> list[dict]:
    """Đọc dữ liệu đơn hàng từ file JSON thật."""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@mcp.tool()
def get_order_details(order_id: str) -> str:
    """Tra cứu thông tin chi tiết một đơn hàng theo mã (order_id).
    
    Args:
        order_id: Mã đơn hàng cần tra cứu (ví dụ: 'ORD-101', 'ORD-102', 'ORD-103').
    """
    orders = load_orders()
    target_id = order_id.strip().upper()
    for order in orders:
        if order["id"].upper() == target_id:
            return json.dumps(order, ensure_ascii=False, indent=2)
            
    return f"❌ Không tìm thấy đơn hàng có mã '{order_id}'. Vui lòng kiểm tra lại mã đơn."

@mcp.tool()
def search_orders_by_status(status: str, limit: int = 5) -> str:
    """Tìm kiếm và lọc danh sách đơn hàng theo trạng thái.
    
    Args:
        status: Trạng thái đơn hàng ('pending', 'shipping', 'delivered', 'cancelled').
        limit: Số lượng đơn hàng tối đa cần lấy (mặc định: 5).
    """
    orders = load_orders()
    target_status = status.strip().lower()
    results = [o for o in orders if o.get("status", "").lower() == target_status]
    results = results[:limit]
    
    if not results:
        return f"ℹ️ Không có đơn hàng nào ở trạng thái '{status}'."
        
    return json.dumps({
        "status_filter": status,
        "total_matched": len(results),
        "orders": results
    }, ensure_ascii=False, indent=2)

@mcp.tool()
def calculate_revenue(status: str = "delivered") -> str:
    """Tính tổng doanh thu và thống kê số lượng đơn hàng theo trạng thái.
    
    Args:
        status: Trạng thái cần tính doanh thu (mặc định: 'delivered').
    """
    orders = load_orders()
    target_status = status.strip().lower()
    matched = [o for o in orders if o.get("status", "").lower() == target_status]
    
    total_amount = sum(o.get("total_amount", 0) for o in matched)
    total_discount = sum(o.get("discount", 0) for o in matched)
    
    return json.dumps({
        "status": status,
        "order_count": len(matched),
        "total_revenue_vnd": total_amount,
        "total_discount_vnd": total_discount,
        "formatted_revenue": f"{total_amount:,} VNĐ"
    }, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # Chạy server ở chế độ giao tiếp chuẩn stdio cho MCP client
    mcp.run()
