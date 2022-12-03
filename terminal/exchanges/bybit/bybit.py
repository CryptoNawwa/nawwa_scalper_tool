import os

from .bybit_tools import PositionStreamData, filter_postion_with_zero_size
from .bybit_tools import ensure_http_result, build_scale_orders, ScaleOrder, build_single_tp_order, filter_postion_with_zero_size
from json_loader import JSON_CONFIG
from abstract.symbols_info import Symbol
from abstract.single_tp_order_data import SingleTpOrder
from abstract.symbol_price_info import SymbolPriceInfo
from abstract.positions_info import Position
from abstract.scale_order_data import ScaleOrdersData
from abstract.auto_take_profit_data import AutoTakeProfitScaleData, AutoTakeProfitSingleTpData
from abstract.exchange import Exchange
from typing import Tuple, cast

from pybit import usdt_perpetual

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'api_keys.json')
SUCCESS_RETURN = "OK"


class Bybit(Exchange):
    def __init__(self) -> None:
        super().__init__()
        self.config = JSON_CONFIG(CONFIG_PATH)
        self.endpoint = "https://api.bybit.com"

        # Init class var #
        self.active_symbol_name: str | None = None
        self.active_symbol_latest_price: SymbolPriceInfo | None = None

        self.current_active_positions: list[Position] = []
        self.symbols: list[Symbol] = []
        
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
        if self.config.data.BybitApiKey is None or self.config.data.BybitSecretApiSecret is None:
            raise ValueError("Missing Bybit api keys or secrets in conf.json file")
        self.websocket_auth_client = usdt_perpetual.WebSocket(
            test=False,
            api_key=self.config.data.BybitApiKey,
            api_secret=self.config.data.BybitSecretApiSecret,
            domain="bytick")

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
        self.symbols = cast(list[Symbol], (self.http_client.query_symbol()).get("result"))
    
    def _get_current_position_for_symbol(self, new_symbol : str) -> None:
        """ Will call API get current position for this symbol """
        try:
            position_data = ensure_http_result(self.http_client.my_position(symbol=new_symbol))

            open_position_list = filter_postion_with_zero_size(position_data.get("result"))

            self.current_active_positions = open_position_list if open_position_list else []

        except Exception as z:
            self.debug_log.append(str(z))
            return

    def _send_limit_orders(self, orders: list[ScaleOrder]) -> Tuple[bool, str]:
        """ Will call API and send scale orders """
        for order in orders:
            ret = self.http_client.place_active_order(
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


    def _get_auto_tp_orders(self, new_position: Position, ticker_info: Symbol, 
                            auto_tp_data: AutoTakeProfitScaleData | AutoTakeProfitSingleTpData) -> list[ScaleOrder]:
                
        # ugly check bcs python does not have type checking on dict
        # scale orders - 
        if auto_tp_data.get("number_of_orders") is not None:
            return build_scale_orders(
                [new_position],
                ticker_info,
                auto_tp_data.get("number_of_orders"),  # type: ignore
                auto_tp_data.get("scale_from"), # type: ignore
                auto_tp_data.get("scale_to")) # type: ignore

        # single tp order
        elif auto_tp_data.get("percent_away") is not None:
            return [build_single_tp_order(
                [new_position],
                ticker_info,
                auto_tp_data.get("percent_away"))] # type: ignore
      
        raise ValueError(f"Wrong auto_tp_data_type, should never happend")


    def _do_auto_tp_system(self, new_position: Position):
        """ Will get the position info and shortcuts cmd and set the appropriate scale orders"""
        try:
            ticker = new_position.get("symbol")
            ticker_info = next((info for info in self.symbols
                                if info["name"] == ticker), None)

            if (ticker is None) or (ticker_info is None) or (self.auto_tp_data is None):
                raise ValueError(f"Missing data to create autotp for {ticker}")


            if self.auto_tp_data.get('auto_cancel_orders') == True:
                try:
                    # cancel active orders before place tp orders
                    self.http_client.cancel_all_active_orders(symbol=ticker)
                except Exception as z:
                    self.debug_log.append("No active orders to cancel")

            # build & send orders based auto_tp_data type
            success, msg = self._send_limit_orders(self._get_auto_tp_orders(new_position, ticker_info, self.auto_tp_data))

            if success is False:
                raise Exception(msg)

        except Exception as e:
            self.debug_log.append(str(e))

    def _trigger_auto_tp_system(self, previous_positions: list[Position]):

         # return if no auto tp needed
        if self.auto_tp_data is None:
            self.debug_log.append("_handle_auto_tp_system : auto_tp_data is None")
            return

        # find new position or same position but with > size (martingale) by doing a diff with the previous list of positions
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

    def _callback_listen_to_position(self, exchange_msg: PositionStreamData | None) -> None:
        """ Called everytime we get into a position """
        
        if (exchange_msg is None):
            self.debug_log.append("_callback_listen_to_position -> none exchange_msg")
            return

        new_positions_from_websocket = exchange_msg.get("data")

        if not exchange_msg or not new_positions_from_websocket:
            self.debug_log.append("_callback_listen_to_position no exchange_msg")
            return

        # filter out closed position (bybit call this event when we close a position, with a size of 0 lol)
        open_position_list = filter_postion_with_zero_size(new_positions_from_websocket)

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

    def exit(self):
        print("Goodbye :)")

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

            return self._send_limit_orders(build_scale_orders(
                self.current_active_positions,
                cast(Symbol, ticker_info),
                number_of_orders,
                scale_from,
                scale_to))
        except Exception as e:
            self.debug_log.append("Error in place_scale_orders" + str(e))
            return False, str(e)

    def terminal_cmd_send_single_tp_order(self, single_tp_data: SingleTpOrder) -> Tuple[bool, str]:
        """ Place one tp order based on parameters """
        try:
            ticker_info = next((info for info in self.symbols
                                if info["name"] == self.active_symbol_name), None)

            if ticker_info is None:
                raise ValueError(f"Missing ticker info to single tp order")

            percent_away = single_tp_data.get("percent_away")
    
            return self._send_limit_orders([build_single_tp_order(
                self.current_active_positions,
                cast(Symbol, ticker_info),
                percent_away)])
        except Exception as e:
            self.debug_log.append("Error in terminal_cmd_set_single_tp_order" + str(e))
            return False, str(e)
