from typing import List, TypedDict


# This was made from Bybit api doc, might not be optimal #

class LotSizeFilter(TypedDict):
    max_trading_qty: float
    min_trading_qty: float
    qty_step: float
    post_only_max_trading_qty: float


class PriceFilter(TypedDict):
    min_price: str
    max_price: str
    tick_size: str


class Symbol(TypedDict):
    name: str
    price_scale: int
    price_filter: PriceFilter
    lot_size_filter: LotSizeFilter

