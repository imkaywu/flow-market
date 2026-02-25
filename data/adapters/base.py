from abc import ABC, abstractmethod
from typing import List, Optional

from data.normalize import Bar


class MarketDataAdapter(ABC):
    @abstractmethod
    def fetch_latest_bars(
        self, symbols: list[str], since: Optional[str]
    ) -> List[Bar]:
        pass
