import re
import json
from typing import (
    Optional, Literal,Tuple, List, Dict, Set
)
from abc import ABC, abstractmethod
from rapidfuzz import process, fuzz

from src.utils import LOGGER

class BaseResolver(ABC):

    market_name = ["코스피", "코스닥", "코넥스"]

    def __init__(self):
        self.stk_stock_to_ticker = {}
        self.ksq_stock_to_ticker = {}
        self.knx_stock_to_ticker = {}

        self.stk_ticker_to_stock = {}
        self.ksq_ticker_to_stock = {}
        self.knx_ticker_to_stock = {}

        self.stk_ord_stocks, self.stk_pre_stocks = [], []
        self.ksq_ord_stocks, self.ksq_pre_stocks = [], []
        self.knx_ord_stocks, self.knx_pre_stocks = [], []

    @abstractmethod
    def _set_stock_list(self, file: str):
        pass

    @abstractmethod
    def _set_stock_to_ticker(self, file: str):
        pass

    @abstractmethod
    def _set_ticker_to_stock(self, file: str):
        pass

    def _check_preferred_stocks(self, stock: str) -> bool:
        """ Check if the stock is a preferred stock"""
        if "우선주" in stock or stock[-1] == "우":
            return True
        if re.search(r"우[A-Z]$", stock):
            return True
        return False

    def _get_most_similar_stock(
            self,
            target: str,
            stocks: List[str]
        ) -> Tuple[str, float, int]:
        """ Get the most similar stock with RapidFuzz """
        if not stocks:
            return ("", -1, -1)
        candidates = process.extract(target.lower(), stocks, scorer=fuzz.ratio)
        return candidates[0]

    def resolve_stock(
            self,
            stock: str,
            market: Literal["코스피", "코스닥", "코넥스", "알수없음"] = "알수없음"
        ) -> Tuple[str, str]:
        """ Resolve stock by stock name and return a ticker """
        LOGGER.info(f"[Resolver] Resolving by stock name: {stock}")
        markets = [market] if market != "알수없음" else self.market_name

        max_score = 0
        resolved_stock: str = None
        resolved_market: tuple = (None, None)
        resolved_ticker: str = None

        for market in markets:
            match market:
                case "코스피":
                    if self._check_preferred_stocks(stock):
                        pool = self.stk_pre_stocks
                    else:
                        pool = self.stk_ord_stocks
                    name, score, _ = self._get_most_similar_stock(stock, pool)

                    if score > max_score:
                        max_score = score
                        resolved_stock = name
                        resolved_market = ("stk","KOSPI")
                        resolved_ticker = self.stk_stock_to_ticker[resolved_stock]

                case "코스닥":
                    if self._check_preferred_stocks(stock):
                        pool = self.ksq_pre_stocks
                    else:
                        pool = self.ksq_ord_stocks
                    name, score, _ = self._get_most_similar_stock(stock, pool)

                    if score > max_score:
                        max_score = score
                        resolved_stock = name
                        resolved_market = ("ksq","KOSDAQ")
                        resolved_ticker = self.ksq_stock_to_ticker[resolved_stock]

                case "코넥스":
                    if self._check_preferred_stocks(stock):
                        pool = self.knx_pre_stocks
                    else:
                        pool = self.knx_ord_stocks
                    name, score, _ = self._get_most_similar_stock(stock, pool)

                    if score > max_score:
                        max_score = score
                        resolved_stock = name
                        resolved_market = ("knx","KONEX")
                        resolved_ticker = self.knx_stock_to_ticker[resolved_stock]

        LOGGER.info(f"[Resolver] Resolved '{stock}' to '{resolved_stock}' in {resolved_market[1]}.")
        return resolved_ticker, resolved_market[0]

    def resolve_ticker(
            self,
            ticker: str,
            market: Literal["코스피", "코스닥", "코넥스", "알수없음"] = "알수없음"
        ) -> Tuple[Optional[Tuple[str, ...]], Optional[str]]:
        """ Resolve stock by ticker """
        markets = [market] if market != "알수없음" else self.market_name

        for market in markets:
            match market:
                case "코스피":
                    stocks: tuple = self.stk_ticker_to_stock.get(ticker)
                    if stocks:
                        return (stocks, "stk")

                case "코스닥":
                    stocks: tuple = self.ksq_ticker_to_stock.get(ticker)
                    if stocks:
                        return (stocks, "ksq")

                case "코넥스":
                    stocks: tuple = self.knx_ticker_to_stock.get(ticker)
                    if stocks:
                        return (stocks, "knx")

        LOGGER.info(f"[Resolver] Failed to resolve a ticker '{ticker}'.")
        return None, None


class KrxStockInfoResolver(BaseResolver):

    resolver_name = "Stock-Info-Resolver"

    def __init__(self):
        super().__init__()
        stk_data = self._load_file('stock_info_kospi.json')
        ksq_data = self._load_file('stock_info_kosdaq.json')
        knx_data = self._load_file('stock_info_konex.json')

        self.stk_stock_to_ticker = self._set_stock_to_ticker(stk_data)
        self.ksq_stock_to_ticker = self._set_stock_to_ticker(ksq_data)
        self.knx_stock_to_ticker = self._set_stock_to_ticker(knx_data)

        self.stk_ticker_to_stock = self._set_ticker_to_stock(stk_data)
        self.ksq_ticker_to_stock = self._set_ticker_to_stock(ksq_data)
        self.knx_ticker_to_stock = self._set_ticker_to_stock(knx_data)

        self.stk_ord_stocks, self.stk_pre_stocks = self._set_stock_list(stk_data)
        self.ksq_ord_stocks, self.ksq_pre_stocks = self._set_stock_list(ksq_data)
        self.knx_ord_stocks, self.knx_pre_stocks = self._set_stock_list(knx_data)

    def _load_file(self, file: str) -> Dict[str, str]:
        """ Load a JSON file """
        try:
            with open(file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data
        except:
            LOGGER.error(f"[{self.resolver_name}] Failed to open the JSON file: {file}")
            return {}

    def _set_stock_list(
            self,
            data: Dict[str, Dict[str, str]]
        ) -> Tuple[List[str], List[str]]:
        """ Set ordinary stock list and preferred stock list """
        ord_stock_lst = []
        pre_stock_lst = []
        for stock, _ in data.items():
            if stock[-1] == "우" or re.search(r"우[A-Z]$", stock):
                pre_stock_lst.append(stock.lower())
            else:
                ord_stock_lst.append(stock.lower())
        return ord_stock_lst, pre_stock_lst

    def _set_stock_to_ticker(
            self,
            data: Dict[str, Dict[str, str]]
        ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """ Set table mapping stock name to ticker """
        stock_to_ticker = {}
        for stock, info in data.items():
            ticker = info['short_code']
            stock_to_ticker[stock.lower()] = ticker
        return stock_to_ticker

    def _set_ticker_to_stock(
        self,
        data: Dict[str, Dict[str, str]]
    ) -> Dict[str, Tuple[str, ...]]:
        """Set table mapping stock name to tuple of tickers"""
        ticker_to_stock: Dict[str, Tuple[str, ...]] = {}
        for _, info in data.items():
            stock = info['name_abbr']
            ticker = info['short_code']
            if stock not in ticker_to_stock:
                ticker_to_stock[ticker] = (stock.lower(),)
            else:
                ticker_to_stock[ticker] += (stock.lower(),)
        return ticker_to_stock


class KrxStockPriceResolver(BaseResolver):

    resolver_name = "Stock-Price-Resolver"

    def __init__(self):
        super().__init__()
        stk_data = self._load_file('stock_price_kospi.json')
        ksq_data = self._load_file('stock_price_kosdaq.json')
        knx_data = self._load_file('stock_price_konex.json')

        self.stk_stock_to_ticker = self._set_stock_to_ticker(stk_data)
        self.ksq_stock_to_ticker = self._set_stock_to_ticker(ksq_data)
        self.knx_stock_to_ticker = self._set_stock_to_ticker(knx_data)

        self.stk_ticker_to_stock = self._set_ticker_to_stock(stk_data)
        self.ksq_ticker_to_stock = self._set_ticker_to_stock(ksq_data)
        self.knx_ticker_to_stock = self._set_ticker_to_stock(knx_data)

        self.stk_ord_stocks, self.stk_pre_stocks = self._set_stock_list(stk_data)
        self.ksq_ord_stocks, self.ksq_pre_stocks = self._set_stock_list(ksq_data)
        self.knx_ord_stocks, self.knx_pre_stocks = self._set_stock_list(knx_data)

    def _load_file(self, file: str) -> Dict[str, str]:
        """ Load a JSON file """
        try:
            with open(file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data
        except:
            LOGGER.error(f"[{self.resolver_name}] Failed to open the JSON file: {file}")
            return {}

    def _set_stock_list(
            self,
            data: Dict[str, Dict[str, str]]
        ) -> Tuple[List[str], List[str]]:
        """ Set ordinary stock list and preferred stock list """
        ord_stocks = []
        pre_stocks = []
        for stock, _ in data.items():
            if stock[-1] == "우" or re.search(r"우[A-Z]$", stock):
                pre_stocks.append(stock.lower())
            else:
                ord_stocks.append(stock.lower())
        return ord_stocks, pre_stocks

    def _set_stock_to_ticker(
            self,
            data: Dict[str, str]
        ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """ Set table mapping stock name to ticker """
        stock_to_ticker = {}
        for stock, ticker in data.items():
            stock_to_ticker[stock.lower()] = ticker
        return stock_to_ticker

    def _set_ticker_to_stock(
            self,
            data: Dict[str, str]
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Set table mapping stock name to tuple of tickers"""
        ticker_to_stock: Dict[str, Tuple[str, ...]] = {}
        for stock, ticker in data.items():
            if stock not in ticker_to_stock:
                ticker_to_stock[ticker] = (stock.lower(),)
            else:
                ticker_to_stock[ticker] += (stock.lower(),)
        return ticker_to_stock