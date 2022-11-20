

from typing import cast
from exchange.symbol_price_info import SymbolPriceInfo

def transform_symbol_info(symbol_infos: dict):
    data = symbol_infos.get("data")
    return cast(SymbolPriceInfo, 
        {
            "symbol" : data["s"],
            "last_price" : round(float(data["p"])),
        })
