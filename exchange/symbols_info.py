from typing import List, TypedDict

## This was made from Bybit api doc, might not be optimal ##

class LotSizeFilter(TypedDict):
    max_trading_qty: int
    min_trading_qty: int
    qty_step: int
    post_only_max_trading_qty: str

class PriceFilter(TypedDict):
    min_price: str
    max_price: str
    tick_size: str

class Symbol(TypedDict):
    name: str
    price_filter: PriceFilter
    lot_size_filter: LotSizeFilter


class SymbolsInfo(TypedDict):
    # ret_code=0 and ext_code="" means  success
    # ret_code=0 and ext_code!="" means success but some parameters were not set correctly
    # ret_code !=0 means fail
    # ret_msg str message 
    # ext_code means error code (not really used kekLmao)
    ret_code: int
    ret_msg: str
    ext_code: str
    result: List[Symbol]