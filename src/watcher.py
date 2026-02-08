import time
import threading
from datetime import datetime
from typing import Callable, Optional
from src.utils import KST, LOGGER

class KrxDateWatcher:

    def __init__(self,
        callback: Callable[[str], None],
        interval: int = 30
    ) -> None:
    
        self.today = datetime.now(KST).date()
        self.on_new_date = callback
        self.interval: int = interval

        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None

    def run(self) -> None:
        """Run scheduler in another thread."""
        if self.thread and self.thread.is_alive():
            return

        LOGGER.info("[Date Watcher] KRX Date Watcher started")
        self.thread = threading.Thread(
            target=self._watch_date_change,
            daemon=True,
        )
        self.thread.start()

    
    def stop(self) -> None:
        """Stop the date watcher thread."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
        LOGGER.info("[Date Watcher] KRX Date Watcher stopped")

    
    def _watch_date_change(self) -> None:
        """Watch current date change"""
        while not self.stop_event.is_set():
            try:
                LOGGER.info(f"[Date Watcher] Current Date: {self.today} (KST)")
                current_date = datetime.now(KST).date()
                if current_date != self.today:
                    self.on_new_date()
                    self.today = current_date
                    LOGGER.info(f"[Date Watcher] Current Date updated: {current_date} (KST)")

            except Exception as e:
                LOGGER.exception(f"[Date Watcher] Exception Occured: {e}")

            time.sleep(self.interval)