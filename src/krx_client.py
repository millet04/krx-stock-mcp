import os
import aiohttp
import requests
from typing import Dict, Any
from src.utils import LOGGER

class KrxStockClient:

    async def make_request(self, url: str) -> Dict[str, Any]:
        headers = {}
        if api_key := os.environ.get("KRX_API_KEY"):
            headers["AUTH_KEY"] = api_key

        async with aiohttp.ClientSession() as client:
            try:
                async with client.get(url, headers=headers, timeout=5.0) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                LOGGER.exception(f"[KRX API] API request failed.Check if the url is valid: {url}")
                return {}
        

    def make_request_sync(self, url: str) -> Dict[str, Any]:
        headers = {}
        if api_key := os.environ.get("KRX_API_KEY"):
            headers["AUTH_KEY"] = api_key
        try:
            response = requests.get(url, headers=headers, timeout=5.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            LOGGER.exception(f"[KRX API] API request failed. Check if the url is valid: {url}")
            return {}


    async def fetch_stock_info(
        self,
        date: str,
        market: str
    ) -> Dict[str, Dict[str, Any]]:
        """Request stock inofrmation from API"""
        if market not in ["stk", "ksq", "knx"]:
            raise ValueError("Market must be the one of 'stk', 'ksq', or 'knx'.")
        
        url = f"http://data-dbg.krx.co.kr/svc/apis/sto/{market}_isu_base_info?basDd={date}"
        data = await self.make_request(url)
        
        records = data.get("OutBlock_1", [])
        if not records:
            LOGGER.error(f"[KRX API] No market data found from API. Check if the date ({date}) is valid.")

        return {record['ISU_NM']:record for record in records}
        

    async def fetch_stock_info_sync(
        self,
        date: str,
        market: str
    ) -> Dict[str, Dict[str, Any]]:
        """Request stock inofrmation from API"""
        if market not in ["stk", "ksq", "knx"]:
            raise ValueError("Market must be the one of 'stk', 'ksq', or 'knx'.")
        
        url = f"http://data-dbg.krx.co.kr/svc/apis/sto/{market}_isu_base_info?basDd={date}"
        data = await self.make_request_sync(url)
        
        records = data.get("OutBlock_1", [])
        if not records:
            LOGGER.error(f"[KRX API] No market data found from API. Check if the date ({date}) is valid.")
                    
        return {record['ISU_NM']:record for record in records}


    async def fetch_stock_price(
        self,
        date: str,
        market: str
    ) -> Dict[str, Dict[str, Any]]:
        """Request stock price from API"""
        if market not in ["stk", "ksq", "knx"]:
            raise ValueError("Market must be the one of 'stk', 'ksq', or 'knx'.")
        
        url = f"http://data-dbg.krx.co.kr/svc/apis/sto/{market}_bydd_trd?basDd={date}"
        data = await self.make_request(url)
        
        records = data.get("OutBlock_1", [])
        if not records:
            LOGGER.error(f"[KRX API] No market data found from API. Check if the date ({date}) is valid.")
        
        return {record['ISU_NM']:record for record in records}


    async def fetch_stock_price_sync(
        self,
        date: str,
        market: str
    ) -> Dict[str, Dict[str, Any]]:
        """Request stock price from API"""
        if market not in ["stk", "ksq", "knx"]:
            raise ValueError("Market must be the one of 'stk', 'ksq', or 'knx'.")
        
        url = f"http://data-dbg.krx.co.kr/svc/apis/sto/{market}_bydd_trd?basDd={date}"
        data = await self.make_request_sync(url)
        
        records = data.get("OutBlock_1", [])
        if not records:
            LOGGER.error(f"[KRX API] No market data found from API. Check if the date ({date}) is valid.")
        
        return {record['ISU_NM']:record for record in records}  