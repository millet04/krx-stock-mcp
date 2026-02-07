import sys
import json
from collections import defaultdict
from typing import Optional, Literal
from krx_client import KrxStockClient
from cache import KrxStockInfoCache, KrxStockPriceCache
from watcher import KrxDateWatcher

from schema import ToolRequestModel
from utils import get_latest_open_date, LOGGER

from fastmcp import FastMCP


class KrxStockServer:

    def __init__(self, args):
        self.mcp = FastMCP(args.server_name)
        self.client = KrxStockClient()
        self.si_cache = KrxStockInfoCache(max_size=args.si_cache_size)
        self.sp_cache = KrxStockPriceCache(max_size=args.sp_cache_size)
        self.watcher = KrxDateWatcher(
            callback = self._on_new_open_date,
            interval = 30,
        )

        self.market_mapper = {
            "코스피":"stk",
            "코스닥":"ksq",
            "코넥스":"knx"
        }

    def register_mcp_primitives(self) -> None:
        """Register defined MCP primitives"""
        self._register_get_stock_info_by_date()
        self._register_get_stock_price_by_date()
        self._register_get_time_range_by_market()


    def run_server(self, kwargs) -> None:
        """Run MCP Server with scheduler"""        
        try:
            LOGGER.info(f"[Server] Server is running...")
            self.watcher.run()
            self.mcp.run(**kwargs)
        except Exception as e:
            LOGGER.exception(f"[Server] Fatal error occurred")
            self.stop_server()


    def stop_server(self) -> None:
        """Stop MCP Server with scheduler"""
        LOGGER.info("[Server] Stopping server components")
        self.watcher.stop()
        sys.exit(1)


    def _on_new_open_date(self) -> None:
        """A callback function to update the latest opening date"""
        latest_date =  get_latest_open_date()
        LOGGER.info(f"[Server] Latest Available Date in KRX API: {latest_date}")

        if self.si_cache.latest_date != latest_date:
            si_latest_dict = defaultdict(dict)
            for market in self.market_mapper.keys():
                si_latest = self.client.fetch_stock_info_sync(latest_date, market)
                si_latest_dict[(latest_date, market)] = si_latest
            self.si_cache.update_latest(latest_date, si_latest_dict)

        if self.sp_cache.latest_date != latest_date:
            sp_latest_dict = defaultdict(dict)
            for market in self.market_mapper.keys():
                sp_latest = self.client.fetch_stock_info_sync(latest_date, market)
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


    def _register_get_stock_info_by_date(self) -> None:
        """A wrapper function for a MCP tool defined inside"""
        @self.mcp.tool()
        async def get_stock_info_by_date(
            request: ToolRequestModel 
        ) -> str:
            """
            한국거래소(KRX) API를 활용해 사용자가 요구한 날짜의 주식 종목별 '기본 정보'를 조회합니다.
        
            <주의사항>
            - 사용자가 당일 정보를 요구하거나 사용자의 질의에 날짜 정보가 없으면, 전일 기준으로 조회합니다.
            - 사용자가 요구하는 종목이 '우선주'라는 언급이 없으면, '보통주'로 처리한다. 예) 삼성전자 -> 삼성전자보통주
            - 한국거래소 API 사용 규정상, 출력에 어떠한 추가적인 설명이나 해설을 제시해서는 안 된다.  

            Args:
                request (ToolRequestModel): 종목 기본 정보 조회를 위한 파라미터 모델
                - request.stock (str): 기본 정보를 조회할 주식 종목명
                - request.market (Literal['코스피','코스닥','코넥스','알수없음']): 조회할 주식이 속한 주식 시장. 판단이 어려울 경우 '알수없음'을 전달.
                - request.date (Optional[str]): 조회 기준 날짜 문자열 (예: '20250627'). 판단이 어려울 경우 None을 전달.
    
            Returns:
                str: 조회된 종목들의 거래 정보를 종합해 MarkDown 형식으로 반환한다.
                     유효한 정보가 없을 경우, 이 사실을 알리는 문자열을 반환한다.
            """
            return await self.get_stock_info(
                stock=request.stock,
                market=request.market,
                date=request.date,
            )


    def _register_get_stock_price_by_date(self) -> None: 
        """A wrapper function for a MCP tool defined inside"""
        @self.mcp.tool()
        async def get_stock_price_by_date(
            request: ToolRequestModel 
        ) -> str:
            """
            한국거래소(KRX) API를 활용해 사용자가 요구한 날짜의 주식 종목별 '기본 정보'를 조회한다.
    
            <주의사항>
            - 사용자가 당일 정보를 요구하거나 사용자의 질의에 날짜 정보가 없으면, 전일 기준으로 조회한다.
            - 사용자가 요구하는 종목이 우선주라는 언급이 없으면, 보통주로 처리한다. 예) 삼성전자 -> 삼성전자보통주
            - 한국거래소 API 사용 규정상, 출력에 어떠한 추가적인 설명이나 해설을 제시해서는 안 된다.        

            Args:
                request (ToolRequestModel): 종목 주가 정보 조회를 위한 파라미터 모델
                - request.stock (str): 기본 정보를 조회할 주식 종목명
                - request.market (Literal['코스피','코스닥','코넥스','알수없음']): 조회할 주식이 속한 주식 시장. 판단이 어려울 경우 '알수없음'을 전달.
                - request.date (Optional[str]): 조회 기준 날짜 문자열 (예: '20250627'). 판단이 어려울 경우 None을 전달.
    
            Returns:
                str: 조회된 종목들의 기본 정보를 종합해 MarkDown 표로 반환합니다.
                     유효한 정보가 없을 경우, 이 사실을 알리는 문자열을 반환합니다.
            """
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

        markets = [market] if market != '알수없음' else list(self.market_mapper.keys())

        for mkt in markets:
            mkt_code = self.market_mapper[mkt]
            target = self.si_cache.get(date, mkt_code, stock)             
            if target:
                return json.dumps(target)
                
        for mkt in markets:
            mkt_code = self.market_mapper[mkt]
            stock_info = await self.client.fetch_stock_info(date, mkt_code)
            target = stock_info.get(stock, {})
            if target:
                self.si_cache.push(date, mkt_code, stock_info)
                return json.dumps(target)

        return json.dumps({})
            
    
    async def get_stock_price(
        self,
        stock: str,
        market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
        date: Optional[str] = None,
    ) -> str:
        """Return stock price information from API"""               
        if not date:
            date = get_latest_open_date()

        markets = [market] if market != '알수없음' else list(self.market_mapper.keys())

        for mkt in markets:
            mkt_code = self.market_mapper[mkt]
            target = self.sp_cache.get(date, mkt_code, stock)
            if target:
                return json.dumps(target)
                
        for mkt in markets:
            mkt_code = self.market_mapper[mkt]
            stock_price = await self.client.fetch_stock_price(date, mkt_code)
            target = stock_price.get(stock, {})
            if target:
                self.sp_cache.push(date, mkt_code, stock_price)
                return json.dumps(target)

        return json.dumps({})