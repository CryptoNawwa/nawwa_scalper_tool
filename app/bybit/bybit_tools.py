import math
from app.exchange.positions_info import Position
from app.exchange.symbols_info import Symbol
from typing import Literal, TypedDict


class ScaleOrder(TypedDict):
    symbol: str
    side: Literal["Buy", "Sell"]
    order_type: str
    qty: int
    price: float
    time_in_force: str
    reduce_only: bool
    close_on_trigger: bool
    position_idx: int


def ensure_http_result(http_result: dict) -> dict:
    """ Take HTTP response and throw appropriate error """
    # ret_code=0 and ext_code="" means create order success
    # ret_code=0 and ext_code!="" means create order success but some parameters were not set correctly
    # ret_code !=0 means create order fail
    # ext_code means please refer to Errors

    dict_http_result = dict(http_result)
    ret_code = int(dict_http_result.get("ret_code"))
    ext_code = dict_http_result.get("ext_code")

    if ret_code == 0 and ext_code != "":
        raise Exception(f"Wrong parameters, code :{ext_code}")
    if ret_code != 0:
        raise Exception(f"Bybit API error {ret_code} - {ext_code}")
    return dict_http_result


def remove_space_and_split(string: str) -> list[str]:
    return " ".join(string.split()).split(" ")


def round_to_tick(value: float, tick_size: float) -> float:
    return math.ceil(value / tick_size) * tick_size


def build_scale_orders(
        current_positions: list[Position] | None,
        ticker_info: Symbol,
        number_of_orders: int,
        scale_from: float,
        scale_to: float) -> list[ScaleOrder]:
    # Safeguards #
    if current_positions is None:
        raise ValueError("You don't have any position opened")
    elif ticker_info is None:
        raise ValueError("Cannot find ticker info")

    # Get current position data #
    current_position_data = next((pos for pos in current_positions
                                  if pos["symbol"] == ticker_info["name"] and pos["size"] > 0.0), None)

    if current_position_data is None:
        raise ValueError("No current position found")

    # Extract data from ticker info
    ticker_tick_size = float(ticker_info["price_filter"]["tick_size"])
    ticker_price_scale = int(ticker_info["price_scale"])
    min_trad_quant = float(ticker_info["lot_size_filter"]["min_trading_qty"])
    max_trad_quant = float(ticker_info["lot_size_filter"]["post_only_max_trading_qty"])

    # Extract data from current position
    side = str(current_position_data.get("side"))
    entry_price = float(current_position_data.get("entry_price"))
    pos_size = float(current_position_data.get("size"))

    # Calculate qty of token per order
    amount_per_order = pos_size / number_of_orders

    # Guards based on Bybit orderbook
    if amount_per_order < min_trad_quant:
        raise ValueError(f"Scaling too big, min size per limit order : {min_trad_quant}")
    elif amount_per_order > max_trad_quant:
        raise ValueError(f"Scaling too small, max size per limit order : {max_trad_quant}")

    # Calculate starting and ending price of the range (scale)
    entry_to_percent = (entry_price / 100)
    from_value = entry_to_percent * scale_from
    to_value = entry_to_percent * scale_to

    from_price = round_to_tick(entry_price + from_value if side == "Buy" else entry_price - from_value,
                               ticker_tick_size)
    to_price = round_to_tick(entry_price + to_value if side == "Buy" else entry_price - to_value, ticker_tick_size)

    # Calculate step between each scale order
    steps = round_to_tick((to_price - from_price) / (number_of_orders - 1), ticker_tick_size)

    # Create scale order array
    i = 0
    orders: list[dict] = []
    while i < number_of_orders:
        orders.append({
            "symbol": ticker_info["name"],
            "side": "Buy" if side == "Sell" else "Sell",
            "order_type": "Limit",
            "qty": amount_per_order,
            "price": round(from_price + i * steps, ticker_price_scale),
            "time_in_force": "PostOnly",
            "reduce_only": True,
            "close_on_trigger": False,
            "position_idx": 0
        })
        i = i + 1

    # Guard so price never goes above range
    if orders[number_of_orders - 1]["price"] != to_price:
        orders[number_of_orders - 1]["price"] = round(to_price, ticker_price_scale)

    # Return list of dict
    return orders
