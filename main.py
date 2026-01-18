import asyncio
import argparse
from server import KrxStockServer

from dotenv import load_dotenv

load_dotenv()

def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="KRX-Stock MCP Server")
    
    parser.add_argument(
        "--server_name",
        type=str,
        default="krx-stock-mcp",
        help="MCP 서버의 이름"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    server = KrxStockServer(args)
    server.register_mcp_primitives()
    server.run_server()