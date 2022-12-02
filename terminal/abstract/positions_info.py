from typing import Literal, TypedDict


# This was made from Bybit api doc, might not be optimal ##

class Position(TypedDict):
    symbol: str
    entry_price: float
    side: Literal["BUY", "SELL"]
    size: float
