import sys
import json
import asyncio
import argparse
from typing import List, Dict
from urllib.parse import urlunparse
from schema import ToolRequestModel
from utils import LOGGER

from fastmcp import Client


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description="Health Checker for KRX-Stock MCP Server")
    
    parser.add_argument(
        "--server_name",
        type=str,
        default="krx-stock-mcp",
        help="MCP 서버의 이름"
    )
    parser.add_argument(
        "--ip",
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
    
    return parser.parse_args()


class KrxStockHealthChecker:

    def __init__(self, args):
        server_url = urlunparse((
            "http",
            f"{args.ip}:{args.port}",
            "",
            "",
            "",
            ""
        ))
        self.client = Client(server_url)
        self.tools = []


    async def initialize(self):
        """Load available tool list from server"""
        self.tools = await self.client.list_tools()
        LOGGER.info(f"[Health Checker] Available tools: {[t.name for t in self.tools]}")


    async def run_tool_check(self, tool_name: str, entries: List[Dict[str, str]]) -> bool:
        """"""
        if not any(tool.name == tool_name for tool in self.tools):
            LOGGER.error(f"[Health Checker] '{tool_name}' does not exist")
            return False

        for entry in entries:
            try:
                entry_model = ToolRequestModel(
                    stock = entry['stock'],
                    makret = entry['market'],
                    date = entry['date']
                )
                result = await self.client.call_tool(tool_name, {'request':entry_model})
                if not result:
                    LOGGER.error(f"[Health Checker] Health check failed: {tool_name}, entry={entry}")
                    return False
            except Exception as e:
                LOGGER.exception(f"[Health Checker] Exception during health check: {entry}")
                return False

        LOGGER.info(f"[Health Checker] Health check passed for tool '{tool_name}'")
        return True


async def main(args):
    checker = KrxStockHealthChecker(args)
    try:
        with open("health_check_entries.json", "r", encoding="utf-8") as file:
            entries = json.load(file)
    except RuntimeError as e:
        LOGGER.exception(f"Failed to load health check entries: {str(e)}")
        sys.exit(1)
    
    async with checker.client:
        LOGGER.info("[Health Checker] Client Connected")   
        await checker.initialize()
        
        for tool in checker.tools:
            await checker.run_tool_check(tool.name, entries[tool.name])


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))