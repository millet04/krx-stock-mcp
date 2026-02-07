from abc import ABC
from typing import Optional, Dict, Tuple
from collections import OrderedDict
from utils import LOGGER


class BaseCache(ABC):
    """LRU Cache"""
    cache_name = "Base Cache"
    markets = ["stk", "ksq", "knx"]
    
    def __init__(self, max_size: int = 10):
        if max_size < 1:
            raise ValueError(f"[{self.cache_name}] The 'max_size' must be larger than 0")
        
        self._latest_date: str | None = None
        self._latest: Dict[Tuple[str, str], dict] = {}
        self._lru_cache: OrderedDict[Tuple[str, str], dict] = OrderedDict()
        self._max_size: int = max_size
        

    @property
    def latest_date(self) -> Optional[str]:
        return self._latest_date
    
    @latest_date.setter
    def latest_date(self, date: str) -> None:
        self._latest_date = date

    @property
    def latest(self) -> Dict[Tuple[str, str], dict]:
        return self._latest

    @latest.setter
    def latest(self, data: Dict[Tuple[str, str], dict]):
        self._latest = data

    
    def get(self,
            date: str,
            market: str,
            stock: str
        ) -> dict:
        """Get data from LRU cache."""
        markets = [market] if market else self.markets

        if date == self.latest_date:
            for mkt in markets:
                if (date, mkt) in self.latest:
                    LOGGER.info(f"[{self.cache_name}] Hit the latest cache")
                    return self.latest.get((date, mkt), {}).get(stock, {})

        for mkt in markets:
            if (date, mkt) in self._lru_cache:
                if stock in set(self._lru_cache[(date, market)].keys()):
                    LOGGER.info(f"[{self.cache_name}] Hit the LRU cache")
                    self._lru_cache.move_to_end((date, mkt))
                    return self._lru_cache.get((date, mkt), {}).get(stock, {})
        return {}


    def push(self,
             date: str,
             market: str,
             entries: Dict[str, dict]
        ) -> None:
        """
        Push data directly into LRU cache. 
        This method does NOT update latest_date.
        """
        if date is None or market is None or entries is None:
            raise ValueError(f"[{self.cache_name}] The 'date', 'market', and 'entries' must not be None")

        if not isinstance(entries, dict):
            raise TypeError(f"[{self.cache_name}] The 'entries' must be a dictionary type")

        LOGGER.info(f"[{self.cache_name}] Miss the LRU cache and push new data")
        self._lru_cache[(date, market)] = entries
        self._lru_cache.move_to_end((date, market))

        if len(self._lru_cache) > self._max_size:
            self._lru_cache.popitem(last=False)
            LOGGER.info(f"[{self.cache_name}] Removed the last item from the cache")


    def update_latest(self,
                      date: str,
                      entries: Dict[Tuple[str, str], dict]
        ) -> None:
        """ Update the latest date and data. """
        if not isinstance(entries, dict):
            raise TypeError(f"[{self.cache_name}] The 'data' must be a dictionary type")
        
        if self.latest_date and self.latest_date != date:
            self._move_to_lru(self.latest)
            
        self.latest_date = date
        self.latest = entries
        LOGGER.info(f"[{self.cache_name}] Updated the latest date and data")
    

    def _move_to_lru(self,
                     entries: Dict[Tuple[str, str], dict],
        ) -> None:
        """Move outdated latest data into LRU cache."""
        for (date, market), entry in entries.items():
            self._lru_cache[(date, market)] = entry
            self._lru_cache.move_to_end((date, market))
            LOGGER.info(f"[{self.cache_name}] Moved the previous latest data into the Cache ({market})")

            if len(self._lru_cache) > self._max_size:
                self._lru_cache.popitem(last=False)
                LOGGER.info(f"[{self.cache_name}] Removed the last item from the cache")
        
        
class KrxStockInfoCache(BaseCache):
    """Cache storing basic stock information"""
    cache_name = "Stock Info Cache"
    
    def __init__(self, max_size):
        super().__init__(max_size)
    
        
class KrxStockPriceCache(BaseCache):
    """Cache storing stock price"""
    cache_name = "Stock Price Cache"

    def __init__(self, max_size):
        super().__init__(max_size)