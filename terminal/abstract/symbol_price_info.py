from typing import List, TypedDict

## This was made from Bybit api doc, might not be optimal ##

class SymbolPriceInfo(TypedDict):
    symbol: str
    last_price: float