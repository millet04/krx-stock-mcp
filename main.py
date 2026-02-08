import argparse
from src.server import KrxStockServer

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
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="MCP 서버 통신 방식 (stdio/streamable-http)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="MCP 서버의 IP 주소"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="MCP 서버의 포트 번호"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="/",
        help="MCP 서버의 경로"
    )
    parser.add_argument(
        "--si_cache_size",
        type=int,
        default=2,
        help="종목 기본 정보를 담는 캐시의 최대 사이즈"
    )
    parser.add_argument(
        "--sp_cache_size",
        type=int,
        default=2,
        help="종목 주가 정보를 담는 캐시의 최대 사이즈"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    kwargs = {
        "transport": args.transport,
    }
    if args.transport == "streamable-http":
        kwargs.update(
            host=args.host,
            port=args.port,
            path=args.path,
        )

    server = KrxStockServer(args)
    server.register_mcp_primitives()
    server.run_server(kwargs)