import os
from binance_exchange.transformers.transform_symbol_info import transform_symbol_info
from config import Configuration
from exchange.symbols_info import SymbolsInfo, Symbol
from exchange.symbol_price_info import SymbolPriceInfo
from exchange.positions_info import Position
from exchange.scale_order_data import ScaleOrdersData
from exchange.exchange import Exchange
from typing import Tuple, cast

from binance import Client, ThreadedWebsocketManager

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'data/conf.json')
SUCCESS_RETURN = "OK"


class Binance(Exchange):
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
        self.binance_client = self._create_binance_client()
        self.binance_ws = self._create_binance_ws()

        # launch ws and load things
        self._load_binance_symbols()
        self._listen_user_position()

    # Private methods #
    def _create_binance_client(self) -> Client:
        return Client(self.config.data.BinanceApyKey,
                                    self.config.data.BinanceSecretApiSecret)

    def _create_binance_ws(self) -> ThreadedWebsocketManager:
        twm = ThreadedWebsocketManager(api_key=self.config.data.BinanceApyKey,
        api_secret=self.config.data.BinanceSecretApiSecret)

        # start is required to initialise its internal loop
        twm.start()
        return twm

    def _load_binance_symbols(self) -> None:
        self.symbols = self.binance_client.get_all_tickers()


    def _callback_start_user_socket(self, msg):
        self.debug_log.append(msg)
        return

    def _listen_user_position(self):
        ## not working, todo: use https://github.com/LUCIT-Systems-and-Development/unicorn-binance-websocket-api
        ret = self.binance_ws.user_socket(self._callback_start_user_socket)
        self.debug_log.append(ret)

    def _get_symbol_info(self, symbol) -> dict:
        return dict(self.binance_client.get_symbol_info(symbol))

    def _callback_info_price_feed(self, info: any):
        try :
            if info is None:
                return
            
            self.active_symbol_latest_price = transform_symbol_info(dict(info))
            return 
        except Exception as e:
            self.debug_log.append(str(e))


    # Public methods #
    def trigger_quit(self):
        print("stop socket")
        self.binance_ws.stop()

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
                                if info["symbol"] == new_symbol), None)
            # If not, leave
            if symbol_info is None:
                raise ValueError(f"Symbol {new_symbol} not supported by Binance")

            # Set new symbol & symbol data
            self.active_symbol_name = new_symbol
            self.active_symbol_info = self._get_symbol_info(new_symbol)

            # Load current position for this symbol
            #self._get_current_position_for_symbol(new_symbol)

            # Check if ticker already subscribed
            symbol_already_subscribed = next((ticker for ticker in self.already_subscribed_symbol_price
                                if ticker == new_symbol), None)
            
            if symbol_already_subscribed is None:
                self.binance_ws.start_symbol_mark_price_socket(self._callback_info_price_feed,
                            new_symbol, True)
                self.already_subscribed_symbol_price.append(self.active_symbol_name)

            return True, SUCCESS_RETURN
        except Exception as e:
            self.active_symbol_name = None
            self.active_symbol_info = None
            return False, str(e)

    def terminal_cmd_cancel_all_orders(self) -> Tuple[bool, str, int]:
        """ Will cancel all limit orders for current ticker """
        return False, "Not Implemented", 0

    def terminal_cmd_set_scale_orders(self, scale_order_data: ScaleOrdersData) -> Tuple[bool, str]:
        """ Place multiple orders based on parameters """
        return False, "Not Implemented"
