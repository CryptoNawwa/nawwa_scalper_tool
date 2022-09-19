from abc import ABC, abstractmethod

from typing import Tuple

from exchange.auto_take_profit_data import AutoTakeProfitData
from exchange.scale_order_data import ScaleOrdersData
from exchange.positions_info import Position
from exchange.symbol_price_info import SymbolPriceInfo


class Exchange(ABC):
    auto_tp_data: AutoTakeProfitData

    ## Methods for the UI to get info or update data on screen
    @abstractmethod
    def get_active_symbol(self) -> str | None:
        """ Get current active trading symbol  """
        ...

    @abstractmethod
    def get_latest_price_info_for_active_symbol(self) -> SymbolPriceInfo | None:
        """ Get price info for active symbol """
        ...

    @abstractmethod
    def get_current_positions(self) -> list[Position] | None:
        """ Get current active position """
        ...

    @abstractmethod
    def get_error_log(self, flush: bool = True) -> list | None:
        """ Get debug log array to print in log file"""
        ...

    def set_auto_tp_data(self, auto_tp_data: AutoTakeProfitData) -> list | None:
        """ Will be called by UI to set data for auto tp """
        self.auto_tp_data = auto_tp_data

    ## CMD methods
    @abstractmethod
    def terminal_cmd_switch_active_symbol(self, new_symbol: str) -> Tuple[bool, str]:
        """ Cmd to switch active symbol """
        ...

    @abstractmethod
    def terminal_cmd_cancel_all_orders(self) -> Tuple[bool, str, int]:
        """ Cmd to cancel all orders return number of order cancelled"""
        ...

    @abstractmethod
    def terminal_cmd_set_scale_orders(self, scale_order_data: ScaleOrdersData) -> Tuple[bool, str]:
        """ Cmd to place scale orders """
        ...
