import sys
import json
import asyncio
from collections import defaultdict
from typing import Optional, Literal
from src.resolver import KrxStockInfoResolver, KrxStockPriceResolver
from src.krx_client import KrxStockClient
from src.cache import KrxStockInfoCache, KrxStockPriceCache
from src.watcher import AsyncKrxDateWatcher

from src.descriptions.loader import load_description 
from src.schemas.schema import (
    ToolRequestModel,
    StockInfoOutputModel,
    StockPriceOutputModel
)
from src.utils import get_latest_open_date, LOGGER

from fastmcp import FastMCP


class KrxStockServer:

    market_code = ["stk", "ksq", "knx"]
    market_name = ["코스피", "코스닥", "코넥스"]
    
    def __init__(self, args):
        self.mcp = FastMCP(args.server_name)
        self.client = KrxStockClient()
        self.si_cache = KrxStockInfoCache(max_size=args.si_cache_size)
        self.sp_cache = KrxStockPriceCache(max_size=args.sp_cache_size)
        self.si_resolver = KrxStockInfoResolver()
        self.sp_resolver = KrxStockPriceResolver()
        self.watcher = AsyncKrxDateWatcher(
            callback = self.on_new_open_date,
            interval = 30,
            log_interval = 300
        )
        
        if len(self.market_code) != len(self.market_name):
            raise ValueError(
                "The class variables 'market_kor' and 'market_eng' must have the same length."
            )
        
        self.market_mapper = dict(zip(self.market_name, self.market_code))
        
    def register_mcp_primitives(self) -> None:
        """Register defined MCP primitives"""
        self._register_get_stock_info_by_date()
        self._register_get_stock_price_by_date()

    async def run_server(self, kwargs) -> None:
        """Run MCP Server with scheduler asyncronously"""        
        LOGGER.info("[Server] Server is running...")
        try:
            await asyncio.gather(
                self.mcp.run_async(**kwargs),
                self.watcher.async_watch_date_change(),
            )
        except Exception:
            LOGGER.exception("[Server] Fatal error occurred")
        finally:
            LOGGER.info("[Server] Server is shutting down...")
            self.stop_server()
    
    def stop_server(self) -> None:
        """Stop MCP Server with scheduler"""
        LOGGER.info("[Server] Stopping server components")
        sys.exit(1)

    async def on_new_open_date(self) -> None:
        """A callback function to update the latest opening date"""
        latest_date =  get_latest_open_date()
        LOGGER.info(f"[Server] Latest Available Date in KRX API: {latest_date}")

        if self.si_cache.latest_date != latest_date:
            si_latest_dict = defaultdict(dict)
            for market in self.market_code:
                si_latest = await self.client.fetch_stock_info(latest_date, market)
                si_latest_dict[(latest_date, market)] = si_latest
            self.si_cache.update_latest(latest_date, si_latest_dict)

        if self.sp_cache.latest_date != latest_date:
            sp_latest_dict = defaultdict(dict)
            for market in self.market_code:
                sp_latest = await self.client.fetch_stock_info(latest_date, market)
                sp_latest_dict[(latest_date, market)] = sp_latest
            self.sp_cache.update_latest(latest_date, sp_latest_dict)

    def _register_get_stock_info_by_date(self) -> str:
        """A wrapper function for a MCP tool defined inside"""
        @self.mcp.tool(description=load_description(
                path="src/descriptions/get_stock_info_by_date.yaml",
                latest_date=get_latest_open_date()
        ))
        async def get_stock_info_by_date(request: ToolRequestModel) -> str:
            return await self.get_stock_info(
                stock=request.stock,
                ticker=request.ticker,
                market=request.market,
                date=request.date,
            )

    def _register_get_stock_price_by_date(self) -> str: 
        """A wrapper function for a MCP tool defined inside"""
        @self.mcp.tool(description=load_description(
                path="src/descriptions/get_stock_price_by_date.yaml",
                latest_date=get_latest_open_date()
        ))
        async def get_stock_price_by_date(request: ToolRequestModel) -> str:
            return await self.get_stock_price(
                stock=request.stock,
                ticker=request.ticker,
                market=request.market,
                date=request.date,
            )
        
    async def get_stock_info(
        self,
        stock: Optional[str],
        ticker: Optional[str],
        market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
        date: Optional[str] = None
    ) -> str:
        """Return basic stock information from API"""          
        output: dict = {}
        
        if ticker:
            _, mkt_code = self.si_resolver.resolve_ticker(ticker, market)
        elif stock:
            ticker, mkt_code = self.si_resolver.resolve_stock(stock, market)
        
        if not mkt_code:
             return json.dumps(output)

        cached = self.si_cache.get(date, mkt_code, ticker)             
        if cached:
            output = cached
        else:
            date = date or get_latest_open_date()
            stock_info = await self.client.fetch_stock_info(date, mkt_code)
            target = stock_info.get(ticker)
            
            if target:
                self.si_cache.push(date, mkt_code, stock_info)
                output = target
        
        stock_info = StockInfoOutputModel.model_validate(output)
        return stock_info.model_dump_json(exclude_none=True)

    async def get_stock_price(
        self,
        stock: Optional[str],
        ticker: Optional[str],
        market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
        date: Optional[str] = None,
    ) -> str:
        """Return stock price information from API"""               
        output: dict = {}

        if ticker:
            _, mkt_code = self.si_resolver.resolve_ticker(ticker, market)
        elif stock:
            ticker, mkt_code = self.si_resolver.resolve_stock(stock, market)

        if not mkt_code:
             return json.dumps(output)

        cached = self.sp_cache.get(date, mkt_code, ticker)
        if cached:
            output = cached
        else:
            date = date or get_latest_open_date()
            stock_price = await self.client.fetch_stock_price(date, mkt_code)
            target = stock_price.get(ticker)

            if target:
                self.sp_cache.push(date, mkt_code, stock_price)
                output = target

        stock_price = StockPriceOutputModel.model_validate(output)
        return stock_price.model_dump_json(exclude_none=True)