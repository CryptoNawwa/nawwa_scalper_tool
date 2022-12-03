import os

from abstract.symbol_price_info import SymbolPriceInfo
from abstract.exchange import Exchange
from abstract.positions_info import Position
from abstract.scale_order_data import ScaleOrdersData
from abstract.single_tp_order_data import SingleTpOrder
from binance import Client

from unicorn_binance_rest_api.manager import BinanceRestApiManager
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager

from typing import Tuple, cast

from json_loader import JSON_CONFIG
from abstract.symbols_info import Symbol

from .transformers.transform_symbol_info import tr_get_symbols

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'api_keys.json')
SUCCESS_RETURN = "OK"


class Binance(Exchange):
    def __init__(self) -> None:
        super().__init__()
        self.config = JSON_CONFIG(CONFIG_PATH)
        
        self.symbols: list[Symbol] = []
        self.active_symbol_name: str | None = None
        # Debug array #
        self.debug_log = []
        self.unibinance = self._init_binance_client()
        self.ws_unibiannce = self._init_binance_ws()

        #  Call first methods #   
        self._load_symbols()


    def _init_binance_ws(self):
        return BinanceWebSocketApiManager(exchange="binance.com-futures")

    def _init_binance_client(self):
        return BinanceRestApiManager(exchange="binance.com-futures",  # type: ignore
            api_key=self.config.data.BinanceApiKey,
            api_secret=self.config.data.BinanceApiSecret)

    def _load_symbols(self):
        raw_exchange_info = self.unibinance.futures_exchange_info()
        self.symbols = tr_get_symbols(raw_exchange_info)
        self.debug_log.append(self.symbols)

    def _process_user_data_stream(self, stream_data, stream_buffer_name=False):
        self.debug_log.append(stream_data)

    def _listen_to_position(self) -> None:
        self.ws_unibiannce.create_stream('arr', '!userData',
                    api_key=self.config.data.BinanceApiKey, # type: ignore
                    api_secret=self.config.data.BinanceApiSecret, # type: ignore
                    process_stream_data=self._process_user_data_stream)


    def _get_current_position_for_symbol(self, new_symbol : str) -> None:
        """ Will call API get current position for this symbol """
        try:
            position_data = cast(list, self.unibinance.futures_position_information(symbol=new_symbol))

            open_position_list = filter_postion_with_zero_size(position_data.get("result"))
            ## todo lookl why we have array of self.current_active_positions

            self.current_active_positions = open_position_list if open_position_list else []

        except Exception as z:
            self.debug_log.append(str(z))
            return
    ## Public methods ##
    def exit(self):
        self.ws_unibiannce.stop_manager_with_all_streams()
        print("Goodbye :)")

    def get_active_symbol(self) -> str | None:
        """ Get current active trading symbol  """
        return self.active_symbol_name


    def get_latest_price_info_for_active_symbol(self) -> SymbolPriceInfo | None:
        """ Get price info for active symbol """
        return None


    def get_current_positions(self) -> list[Position]:
        """ Get current active position """
        return []


    def get_error_log(self, flush: bool = True) -> list | None:
        if flush:
            copy = self.debug_log.copy()
            self.debug_log = []
            return copy
        return self.debug_log

    #  CMD methods #
    def terminal_cmd_switch_active_symbol(self, new_symbol: str) -> Tuple[bool, str]:
        try:
            # Check if symbol exist
            symbol_info = next((info for info in self.symbols
                                if info["name"] == new_symbol), None)
            # If not, leave
            if symbol_info is None:
                raise ValueError(f"Symbol {new_symbol} not supported by Binance")

            self.active_symbol_name = new_symbol

            # Load current position for this symbol
            self._get_current_position_for_symbol(new_symbol)

            # Check if ticker already subscribed
            symbol_already_subscribed = next((ticker for ticker in self.already_subscribed_symbol_price
                                if ticker == new_symbol), None)

            # connect to price feed
            if symbol_already_subscribed is None:
                self.websocket_no_auth_client.instrument_info_stream(self._callback_symbol_price_feed,
                                                                 self.active_symbol_name)
                self.already_subscribed_symbol_price.append(self.active_symbol_name)

            return True, SUCCESS_RETURN
        except Exception as e:
            self.active_symbol_name = None
            self.active_symbol_info = None
            return False, str(e)

    def terminal_cmd_cancel_all_orders(self) -> Tuple[bool, str, int]:
        """ Cmd to cancel all orders return number of order cancelled"""
        return False, "Not Implemented", 0

    def terminal_cmd_set_scale_orders(self, scale_order_data: ScaleOrdersData) -> Tuple[bool, str]:
        """ Cmd to place scale orders """
        return False, "Not Implemented"

    def terminal_cmd_send_single_tp_order(self, single_tp_data: SingleTpOrder) -> Tuple[bool, str]:
        """ Cmd to place scale orders """
        return False, "Not Implemented"
