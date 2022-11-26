from typing import List, TypedDict


# This was made from Bybit api doc, might not be optimal #

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
    price_scale: int
    price_filter: PriceFilter
    lot_size_filter: LotSizeFilter

