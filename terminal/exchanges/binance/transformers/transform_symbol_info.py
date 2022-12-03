from typing import cast

from abstract.symbol_price_info import SymbolPriceInfo
from abstract.symbols_info import Symbol


def tr_get_symbols(exchange_info: dict):
    raw_symbols = cast(list, exchange_info.get("symbols"))
    
    symbols : list[Symbol] = []
    for s in raw_symbols:
        symbol = cast(Symbol, { 
            "name" : s['symbol'],
            "price_scale": s['pricePrecision'],
            "price_filter": {
                "min_price" : s['filters'][0]['minPrice'],
                "max_price" : s['filters'][0]['maxPrice'],
                "tick_size" : s['filters'][0]['tickSize'],
            },
            "lot_size_filter" : {
                "max_trading_qty" : float(s['filters'][1]['maxQty']),
                "min_trading_qty" : float(s['filters'][1]['minQty']),
                "qty_step" : float(s['filters'][1]['stepSize']),
                "post_only_max_trading_qty" : float(s['filters'][1]['maxQty']),
            }
        })
        symbols.append(symbol)
    return symbols

