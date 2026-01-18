import json
from typing import Optional, Literal
from zoneinfo import ZoneInfo
from krx_client import KrxStockClient
from schema import ToolRequestModel
from utils import get_latest_open_date

from mcp.server.fastmcp import FastMCP

KST = ZoneInfo("Asia/Seoul")

class KrxStockServer:

    def __init__(self, args):
        self.mcp = FastMCP(args.server_name)
        self.client = KrxStockClient()

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


    def run_server(self) -> None:
        """Run MCP Server with scheduler"""        
        try:
            print(f"Server is running...")
            self.mcp.run(transport="stdio")
        except Exception as e:
            print(f"Server error: {e}")
            self.stop_server()


    def stop_server(self) -> None:
        """Stop MCP Server with scheduler"""
        print("Server stopped gracefully.")

    
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

        if market == '알수없음':
            for mkt in list(self.market_mapper.keys()):
                mkt_code = self.market_mapper[mkt]
                stock_info = await self.client.fetch_stock_info(date, mkt_code)
                target = stock_info.get(stock, {})
                if target:
                    break
        else:  
            mkt_code = self.market_mapper[market] 
            stock_info = await self.client.fetch_stock_info(date, mkt_code)
            target = stock_info.get(stock, {})
        
        return json.dumps(target)
            
    
    async def get_stock_price(
        self,
        stock: str,
        market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
        date: Optional[str] = None,
    ) -> str:
        """Return stock price information from API"""               
        if not date:
            date = get_latest_open_date()

        if market == '알수없음':
            for mkt in list(self.market_mapper.keys()):
                mkt_code = self.market_mapper[mkt]
                stock_price = await self.client.fetch_stock_price(date, mkt_code)
                target = stock_price.get(stock, {})
                if target:
                    break
        else:
            mkt_code = self.market_mapper[market]   
            stock_price = await self.client.fetch_stock_price(date, mkt_code)
            target = stock_price.get(stock, {})
            
        return json.dumps(target)