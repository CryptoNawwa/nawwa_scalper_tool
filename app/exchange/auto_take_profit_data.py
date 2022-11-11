from typing import TypedDict


class AutoTakeProfitScaleData(TypedDict):
    number_of_orders: int
    scale_from: float
    scale_to: float

class AutoTakeProfitSingleTpData(TypedDict):
    percent_away: float
