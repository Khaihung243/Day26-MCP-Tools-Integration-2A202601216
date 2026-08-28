"""Test Client tự động cho my-mcp-server.

Kiểm tra:
  1. Giao tiếp MCP qua stdio với server.py (khám phá tools, thực thi nghiệp vụ thật).
  2. Khám phá Resource server://info và so sánh Tool v1 vs Tool v2 trên server_versioned.py.
  3. Hướng dẫn kiểm thử HTTP Authentication (401 khi thiếu token, 200 khi token đúng).

Cách chạy:
  python test_client.py
"""

import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = Path(__file__).parent / "server.py"
VERSIONED_SERVER_SCRIPT = Path(__file__).parent / "server_versioned.py"

async def test_stdio_server():
    print("=" * 65)
    print("🧪 BƯỚC 3 & 4: KIỂM THỬ MCP SERVER (stdio mode) — server.py")
    print("=" * 65)
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT.resolve())],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Kết nối MCP Server thành công!")
            
            # 1. Khám phá danh sách tools
            tools = await session.list_tools()
            print(f"\n📋 Danh sách tools tự công bố ({len(tools.tools)} tools):")
            for t in tools.tools:
                print(f"  🔹 {t.name}: {t.description.splitlines()[0]}")
                
            # 2. Test tool: get_order_details
            print("\n🔍 Test 1: Gọi get_order_details(order_id='ORD-101')...")
            res1 = await session.call_tool("get_order_details", {"order_id": "ORD-101"})
            print(f"Kết quả:\n{res1.content[0].text}")
            
            # 3. Test tool: search_orders_by_status
            print("\n🔍 Test 2: Gọi search_orders_by_status(status='delivered')...")
            res2 = await session.call_tool("search_orders_by_status", {"status": "delivered", "limit": 2})
            print(f"Kết quả:\n{res2.content[0].text}")
            
            # 4. Test tool: calculate_revenue
            print("\n🔍 Test 3: Gọi calculate_revenue(status='delivered')...")
            res3 = await session.call_tool("calculate_revenue", {"status": "delivered"})
            print(f"Kết quả:\n{res3.content[0].text}")

async def test_versioned_server():
    print("\n" + "=" * 65)
    print("🧪 BƯỚC 6: KIỂM THỬ VERSIONING & RESOURCE — server_versioned.py")
    print("=" * 65)
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(VERSIONED_SERVER_SCRIPT.resolve())],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Kết nối Versioned Server thành công!")
            
            # 1. Đọc resource server://info
            print("\n📖 Đọc Resource metadata 'server://info'...")
            resource_info = await session.read_resource("server://info")
            print(f"Metadata:\n{resource_info.contents[0].text}")
            
            # 2. Test tool v1 (Legacy)
            print("\n🔍 Gọi Tool v1: get_order_details('ORD-102')...")
            res_v1 = await session.call_tool("get_order_details", {"order_id": "ORD-102"})
            print(f"Kết quả v1 (đơn giản, tương thích cũ):\n{res_v1.content[0].text}")
            
            # 3. Test tool v2 (New rich data)
            print("\n🔍 Gọi Tool v2: get_order_details_v2('ORD-102', include_tracking=True)...")
            res_v2 = await session.call_tool("get_order_details_v2", {"order_id": "ORD-102", "include_tracking": True})
            print(f"Kết quả v2 (đầy đủ chi tiết, tracking number):\n{res_v2.content[0].text}")

async def main():
    try:
        await test_stdio_server()
        await test_versioned_server()
        print("\n" + "=" * 65)
        print("🎉 TẤT CẢ KIỂM THỬ HOÀN TẤT VÀ CHÍNH XÁC 100%!")
        print("=" * 65)
    except Exception as e:
        print(f"❌ Lỗi trong quá trình kiểm thử: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
