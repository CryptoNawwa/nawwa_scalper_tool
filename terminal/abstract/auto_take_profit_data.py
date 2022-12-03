from typing import TypedDict


class AutoTakeProfitScaleData(TypedDict):
    number_of_orders: int
    scale_from: float
    scale_to: float
    auto_cancel_orders: bool

class AutoTakeProfitSingleTpData(TypedDict):
    percent_away: float
    auto_cancel_orders: bool
