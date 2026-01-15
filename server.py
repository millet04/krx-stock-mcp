import json
from typing import Optional, Literal
from zoneinfo import ZoneInfo
from datetime import date, datetime, timedelta
from krx_client import KrxStockClient

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

    def register_mcp_tools(self) -> None:
        """Register defined MCP tools"""
        self._register_get_stock_info_by_date()
        self._register_get_stock_price_by_date()


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


    def _register_get_stock_info_by_date(self) -> None:
        """A wrapper function for a MCP tool defined inside"""
        @self.mcp.tool()
        async def get_stock_info_by_date(
            stock: str,
            market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
            date: Optional[str] = None,
        ) -> str:
            """
            한국거래소(KRX) API를 활용해 사용자가 요구한 날짜의 주식 종목별 '기본 정보'를 조회합니다.
        
            <주의사항>
            - 사용자가 당일 정보를 요구하거나 사용자의 질의에 날짜 정보가 없으면, 전일 기준으로 조회합니다.
            - 사용자가 요구하는 종목이 '우선주'라는 언급이 없으면, '보통주'로 처리한다. 예) 삼성전자 -> 삼성전자보통주
            - 한국거래소 API 사용 규정상, 출력에 어떠한 추가적인 설명이나 해설을 제시해서는 안 된다.  

            Args:
                stock (str): 기본 정보를 조회할 주식 종목명
                market (Literal['코스피','코스닥','코넥스','알수없음']): 조회할 주식이 속한 주식 시장. 판단이 어려울 경우 '알수없음'을 전달.
                date (Optional[str]): 조회 기준 날짜 문자열 (예: '20250627'). 판단이 어려울 경우 None을 전달.
    
            Returns:
                str: 조회된 종목들의 거래 정보를 종합해 MarkDown 형식으로 반환한다.
                     유효한 정보가 없을 경우, 이 사실을 알리는 문자열을 반환한다.
            """
            return await self.get_stock_info(
                stock=stock,
                market=market,
                date=date,
            )


    def _register_get_stock_price_by_date(self) -> None: 
        """A wrapper function for a MCP tool defined inside"""
        @self.mcp.tool()
        async def get_stock_price_by_date(
            stock: str,
            market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
            date: Optional[str] = None,
        ) -> str:
            """
            한국거래소(KRX) API를 활용해 사용자가 요구한 날짜의 주식 종목별 '기본 정보'를 조회한다.
    
            <주의사항>
            - 사용자가 당일 정보를 요구하거나 사용자의 질의에 날짜 정보가 없으면, 전일 기준으로 조회한다.
            - 사용자가 요구하는 종목이 우선주라는 언급이 없으면, 보통주로 처리한다. 예) 삼성전자 -> 삼성전자보통주
            - 한국거래소 API 사용 규정상, 출력에 어떠한 추가적인 설명이나 해설을 제시해서는 안 된다.        

            Args:
                stock (str): 주가를 조회할 주식 종목명
                market (Literal['코스피','코스닥','코넥스','알수없음']): 조회할 주식이 속한 주식 시장. 판단이 어려울 경우 '알수없음'을 전달.
                date (Optional[str]): 조회 기준 날짜 문자열 (예: '20250627'). 판단이 어려울 경우 None을 전달.
    
            Returns:
                str: 조회된 종목들의 기본 정보를 종합해 MarkDown 표로 반환합니다.
                     유효한 정보가 없을 경우, 이 사실을 알리는 문자열을 반환합니다.
            """
            return await self.get_stock_price(
                stock=stock,
                market=market,
                date=date,
            )
        

    async def get_stock_info(
        self,
        stock: str,
        market: Literal['코스피','코스닥','코넥스','알수없음'] = '알수없음',
        date: Optional[str] = None,
    ) -> str:
        """Return basic stock information from API"""      
        if not date:
            d = datetime.now(KST).date() - timedelta(days=1)
            while d.weekday() >= 5:
                d -= timedelta(days=1)
            date = d.strftime('%Y%m%d')

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
            d = datetime.now(KST).date() - timedelta(days=1)
            while d.weekday() >= 5:
                d -= timedelta(days=1)
            date = d.strftime('%Y%m%d')

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