import os
from bybit.bybit_tools import ensure_http_result, build_scale_orders, ScaleOrder
from config import Configuration
from exchange.symbols_info import SymbolsInfo, Symbol
from exchange.symbol_price_info import SymbolPriceInfo
from exchange.positions_info import Position
from exchange.scale_order_data import ScaleOrdersData
from exchange.exchange import Exchange
from typing import Tuple, cast

from pybit import usdt_perpetual

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'data/conf.json')
SUCCESS_RETURN = "OK"


class Bybit(Exchange):
    def __init__(self) -> None:
        super().__init__()
        self.config = Configuration(CONFIG_PATH)
        self.endpoint = "https://api.bybit.com"

        # Init class var #
        self.active_symbol_name: str | None = None
        self.active_symbol_info: SymbolsInfo | None = None
        self.active_symbol_latest_price: SymbolPriceInfo | None = None

        self.current_active_positions: list[Position] | None = None
        self.symbols: list[dict] | None = None
        
        self.already_subscribed_symbol_price: list[str] = []

        # Debug array #
        self.debug_log = []

        # Create websocket & http handler  #
        self._create_ws_no_auth()
        self._create_ws_auth()
        self._create_http_auth()

        #  Call methods #
        self._load_bybit_symbol()
        self._listen_to_position()

    # Private methods #
    def _create_ws_auth(self) -> None:
        self.websocket_auth_client = usdt_perpetual.WebSocket(
            test=False,
            api_key=self.config.data.BybitApiKey,
            api_secret=self.config.data.BybitSecretApiSecret,
            domain="bybit")

    def _create_ws_no_auth(self) -> None:
        self.websocket_no_auth_client = usdt_perpetual.WebSocket(
            test=False,
            domain="bytick")

    def _create_http_auth(self) -> None:
        self.http_client = usdt_perpetual.HTTP(
            endpoint=self.endpoint,
            api_key=self.config.data.BybitApiKey,
            api_secret=self.config.data.BybitSecretApiSecret)

    def _load_bybit_symbol(self) -> None:
        self.symbols = dict(self.http_client.query_symbol()).get("result")

    def _send_scale_orders(self, orders: list[ScaleOrder]) -> Tuple[bool, str]:
        """ Will call API and send scale orders """
        for order in orders:
            self.http_client.place_active_order(
                symbol=order.get("symbol"),
                side=order.get("side"),
                order_type=order.get("order_type"),
                qty=order.get("qty"),
                price=order.get("price"),
                time_in_force=order.get("time_in_force"),
                reduce_only=order.get("reduce_only"),
                close_on_trigger=order.get("close_on_trigger"),
                position_idx=order.get("position_idx")
            )
        return True, SUCCESS_RETURN

    def _do_auto_tp_system(self, new_position: Position):
        """ Will get the position info and shortcuts cmd and set the appropriate scale orders"""
        try:
            ticker = new_position.get("symbol")
            ticker_info = next((info for info in self.symbols
                                if info["name"] == ticker), None)

            if (ticker is None) or (ticker_info is None) or (self.auto_tp_data is None):
                raise ValueError(f"Missing data to create autotp for {ticker}")

            try:
                # cancel active orders before place tp orders
                self.http_client.cancel_all_active_orders(symbol=ticker)
            except Exception as z:
                self.debug_log.append("No active orders to cancel")

            # build & send scale orders based on shortcut in auto_tp_data
            success, msg = self._send_scale_orders(build_scale_orders(
                [new_position],
                cast(Symbol, ticker_info),
                self.auto_tp_data.get("number_of_orders"),
                self.auto_tp_data.get("scale_from"),
                self.auto_tp_data.get("scale_to")))

            if success is False:
                raise Exception(msg)
        except Exception as e:
            self.debug_log.append(str(e))

    def _trigger_auto_tp_system(self, previous_positions: list[Position]):

        # return if auto_tp_data
        if self.auto_tp_data is None:
            self.debug_log.append("_handle_auto_tp_system : auto_tp_data is None")
            return

        # return if no auto tp needed
        if self.auto_tp_data.get("activated") is False:
            return

            # find new position by looking a prev ones
        new_positions: dict = {}
        for pos in self.current_active_positions:
            pos_symbol = pos.get("symbol")
            existing_pos = next((x for x in previous_positions if x.get("symbol") == pos_symbol), None)
            if (existing_pos is None) or (float(pos.get("size")) > float(existing_pos.get("size"))):
                new_positions[pos_symbol] = pos

        new_positions_as_list = new_positions.items()

        # do the auto tp system
        for new_pos in new_positions_as_list:
            self._do_auto_tp_system(new_pos[1])

    def _callback_listen_to_position(self, exchange_msg: dict | None) -> None:
        """ Called everytime we get into a position """

        if not exchange_msg or not exchange_msg.get("data"):
            self.debug_log.append("_callback_listen_to_position no exchange_msg")
            return

        # cast bybit data it into typed dict
        raw_position_data = cast(list[Position], exchange_msg.get("data"))

        # filter out closed position (bybit call this event when we close a position, with a size of 0 lol)
        open_position_list = list(filter(lambda position: position.get("size") > 0.0, raw_position_data))

        # save previous position
        previous_positions = self.current_active_positions if self.current_active_positions is not None else []

        # set current position to new positions
        self.current_active_positions = open_position_list

        # handle auto tp system
        self._trigger_auto_tp_system(previous_positions)

    def _listen_to_position(self) -> None:
        """ Call _callback_listen_to_position everytime user get into a position """
        self.websocket_auth_client.position_stream(self._callback_listen_to_position)

    def _callback_symbol_price_feed(self, info: dict) -> None:
        """ Called every 100ms to get price feed of ticker """

        # Set data to None if wrong ticker so the UI class stop refreshing for nothing
        if not self.active_symbol_name:
            self.active_symbol_latest_price = None
            return

        symbol_price_info = cast(SymbolPriceInfo, dict(info).get("data"))

        # Set active_symbol_latest_price if symbol 
        if symbol_price_info and symbol_price_info.get("symbol") == self.active_symbol_name:
            self.active_symbol_latest_price = symbol_price_info

    # Public methods #
    def get_active_symbol(self):
        return self.active_symbol_name

    def get_current_positions(self) -> list[Position]:
        """ Get current active position """
        return self.current_active_positions

    def get_error_log(self, flush: bool = True) -> list:
        if flush:
            copy = self.debug_log.copy()
            self.debug_log = []
            return copy
        return self.debug_log

    def get_latest_price_info_for_active_symbol(self) -> SymbolPriceInfo | None:
        """ Get price info for active symbol """
        return self.active_symbol_latest_price

    # Public terminal methods #
    def terminal_cmd_switch_active_symbol(self, new_symbol: str) -> Tuple[bool, str]:
        """ Cmd to switch active symbol """
        try:
            # Check if ticker exist
            symbol_info = next((info for info in self.symbols
                                if info["name"] == new_symbol), None)
            # If not, leave
            if symbol_info is None:
                raise ValueError(f"Symbol {new_symbol} not supported by Bybit")

            # Set new symbol & symbol data
            self.active_symbol_name = new_symbol
            self.active_symbol_info = symbol_info

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
        """ Will cancel all limit orders for current ticker """
        try:
            if self.active_symbol_name is None:
                raise ValueError("No symbol selected")

            result = self.http_client.cancel_all_active_orders(symbol=self.active_symbol_name)

            dict_result = ensure_http_result(result)
            msg = dict_result.get("ret_msg")

            if dict_result.get("result") is None:
                return True, msg, 0

            number_of_order_cancelled = len(dict_result.get("result"))

            return True, msg, number_of_order_cancelled
        except Exception as e:
            self.debug_log.append("Error in cancel_all_orders" + str(e))
            return False, str(e), 0

    def terminal_cmd_set_scale_orders(self, scale_order_data: ScaleOrdersData) -> Tuple[bool, str]:
        """ Place multiple orders based on parameters """
        try:
            ticker_info = next((info for info in self.symbols
                                if info["name"] == self.active_symbol_name), None)

            if ticker_info is None:
                raise ValueError(f"Missing ticker info to put scale orders")

            number_of_orders = scale_order_data.get("number_of_orders")
            scale_from = scale_order_data.get("scale_from")
            scale_to = scale_order_data.get("scale_to")

            return self._send_scale_orders(build_scale_orders(
                self.current_active_positions,
                cast(Symbol, ticker_info),
                number_of_orders,
                scale_from,
                scale_to))
        except Exception as e:
            self.debug_log.append("Error in place_scale_orders" + str(e))
            return False, str(e)
