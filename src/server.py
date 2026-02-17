import sys
import asyncio
from collections import defaultdict
from typing import Optional, Literal
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
        self._register_get_time_range_by_market()


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


    def _register_get_time_range_by_market(self):
        """A wrapper function for a MCP resource defined inside"""
        @self.mcp.resource("resource://time-range")
        def get_time_range_by_market() -> dict:
            """
            KRX API를 통해 정보를 제공할 수 있는 날짜의 범위를 제시합니다.
            코스닥과 코스피는 2010년 1월 4일 ('20100104')부터 현재 기준 하루 전날까지의 정보를 제공합니다. 
            코넥스는 2013년 7월 1일 ('20130701')부터 현재 기준 하루 전날까지의 정보를 제공합니다.
            
            Returns:
                dict: 시장(market), 첫 번째 날(oldest), 마지막 날(latest)의 정보를 포함한 딕셔너리를 반환한다.
            """
            latest = get_latest_open_date()
            return {
                '코스피':{'oldest': "20100104", 'latest': latest},
                '코스닥':{'oldest': "20100104", 'latest': latest},
                '코넥스':{'oldest': "20130701", 'latest': latest},
            }


    def _register_get_stock_info_by_date(self) -> str:
        """A wrapper function for a MCP tool defined inside"""
        @self.mcp.tool(description=load_description(
                path="src/descriptions/get_stock_info_by_date.yaml",
                latest_date=get_latest_open_date()
        ))
        async def get_stock_info_by_date(request: ToolRequestModel) -> str:
            return await self.get_stock_info(
                stock=request.stock,
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
                market=request.market,
                date=request.date,
            )
        

    async def get_stock_info(
        self,
        stock: str,
        market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
        date: Optional[str] = None,
    ) -> str:
        """Return basic stock information from API"""      
        if not date:
            date = get_latest_open_date()

        markets = [market] if market != '알수없음' else self.market_name
        output: dict = {}

        for mkt in markets:
            mkt_code = self.market_mapper[mkt]
            cached = self.si_cache.get(date, mkt_code, stock)             
            if cached:
                output = cached
                break
        
        if not output:
            for mkt in markets:
                mkt_code = self.market_mapper[mkt]
                stock_info = await self.client.fetch_stock_info(date, mkt_code)
                target = stock_info.get(stock, {})
                if target:
                    self.si_cache.push(date, mkt_code, stock_info)
                    output = target
                    break
        
        stock_info = StockInfoOutputModel.model_validate(output)
        return stock_info.model_dump_json(exclude_none=True)
            
    
    async def get_stock_price(
        self,
        stock: str,
        market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
        date: Optional[str] = None,
    ) -> str:
        """Return stock price information from API"""               
        if not date:
            date = get_latest_open_date()

        markets = [market] if market != '알수없음' else self.market_name
        output: dict = {}

        for mkt in markets:
            mkt_code = self.market_mapper[mkt]
            cached = self.sp_cache.get(date, mkt_code, stock)
            if cached:
                output = cached
                break
        
        if not output:
            for mkt in markets:
                mkt_code = self.market_mapper[mkt]
                stock_price = await self.client.fetch_stock_price(date, mkt_code)
                target = stock_price.get(stock, {})
                if target:
                    self.sp_cache.push(date, mkt_code, stock_price)
                    output = target
                    break
        
        stock_price = StockPriceOutputModel.model_validate(output)
        return stock_price.model_dump_json(exclude_none=True)