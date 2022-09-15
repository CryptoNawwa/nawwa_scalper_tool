from array import array
import math
from os import symlink
from typing import List
from config import Configuration, Dict
from pybit import usdt_perpetual
from pybit import spot
from pybit import HTTP

class BybitClient():

    def __init__(self, config: str) -> None:
        self.config = Configuration(config)
        self.endpoint = "https://api.bybit.com"
        
        self.ticker: str | None = None
        self.ticker_info: Dict | None = None
        self.latest_symbol_info: Dict | None = None
        self.current_positions: List[Dict] | None = None
        self.symbols: List[Dict] | None = None
        
        self.__create_ws_no_auth()
        self.__create_ws_auth()
        self.__create_http()
        
        self.__init_listen_position()
        self.__get_bybit_symbols()
    
    
    def __create_ws_auth(self) -> None:
        self.websocket_auth_client = usdt_perpetual.WebSocket(
        test=False,
        api_key=self.config.data.BybitApiKey,
        api_secret=self.config.data.BybitSecretApiSecret,
        domain="bybit")
        
    def __create_ws_no_auth(self) -> None:
        self.websocket_no_auth_client = usdt_perpetual.WebSocket(
        test=False,
        domain="bytick")

    def __create_http(self) -> None:
        self.http_client = usdt_perpetual.HTTP(
        endpoint=self.endpoint,
        api_key=self.config.data.BybitApiKey,
        api_secret=self.config.data.BybitSecretApiSecret)
        
    def __get_bybit_symbols(self):
        self.symbols = Dict(self.http_client.query_symbol()).get("result")
        
    def __handle_instrument_info_stream(self, msg):
        """ Called every 100ms to get price feed of ticker """
        
        # Set data to None if wrong ticker so the UI stop refreshing for nothing
        if not self.ticker:
            self.latest_symbol_info = None
            return
        
        data = Dict(msg).get("data")
        if data and data["symbol"] == self.ticker:
            self.latest_symbol_info = data
        
    def __handle_position_stream(self, msg):
        """ Called everytime we get into a position """
        data: List[Dict] = Dict(msg).get("data")
        self.current_positions = data
            
    def __init_listen_position(self):
        self.websocket_auth_client.position_stream(self.__handle_position_stream)
        
    def switch_ticker(self, new_ticker: str):
        try:
            # Check if ticker exist
            ticker_info = next(info for info in self.symbols 
                                         if info["name"] == new_ticker)
            # If not, leave
            if not ticker_info:
                raise ValueError("Cannot find ticker informations")
            
            # Set new ticker & save ticker info
            self.ticker = new_ticker
            self.ticker_info = ticker_info
            
            # connect to price feed
            self.websocket_no_auth_client.instrument_info_stream(self.__handle_instrument_info_stream, self.ticker)
            
            return True, "OK"
        except Exception as e:
            print("Error in ticker swithing", str(e))
            self.ticker = None
            self.ticker_info = None
            return False, str(e)
    
    def __round_to_tick(self, value: float, tick_size: float) -> float:
        return math.ceil(value / tick_size) * tick_size
        
    def place_scale_orders(self, number_of_orders: int, scale_from: float, scale_to: float):
        try:
            current_position_data = next(pos for pos in self.current_positions 
                                         if pos["symbol"] == self.ticker and pos["size"] > 0.0)
            
            if current_position_data == None:
                raise ValueError("No current position found")
            
            if self.ticker_info == None:
                raise ValueError("Cannot find ticket info") 
            
            ticker_tick_size = float(self.ticker_info.get("price_filter")["tick_size"])
            ticker_price_scale = int(self.ticker_info.get("price_scale"))
            
            side = str(current_position_data.get("side"))
            entry_price = float(current_position_data.get("entry_price"))
            size = float(current_position_data.get("size"))
            
            entry_to_percent = (entry_price / 100)
            
            from_value = entry_to_percent * scale_from
            from_price = entry_price + from_value if side == "Buy" else entry_price - from_value
            
            to_value = entry_to_percent * scale_to
            to_price = entry_price + to_value if side == "Buy" else entry_price - to_value
            
            steps = (to_price - from_price) / number_of_orders
            
            amount_per_order = size / number_of_orders

            acc = 0
            i = 1
            while i <= number_of_orders:
                price = from_price + acc
                self.http_client.place_active_order(
                    symbol=self.ticker,
                    side="Buy" if side == "Sell" else "Sell",
                    order_type="Limit",
                    qty=amount_per_order,
                    price=round(self.__round_to_tick(price, ticker_tick_size), ticker_price_scale),
                    time_in_force="PostOnly",
                    reduce_only=True,
                    close_on_trigger=False,
                    position_idx = 0
                )
                acc = acc + steps
                i = i + 1
            
            
            return True, "OK"
        except Exception as e:
            print("Error in place_scale_orders", str(e))
            return False, str(e)
    
        




