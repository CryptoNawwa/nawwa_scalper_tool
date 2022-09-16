import math
from typing import List, Tuple, Callable
from config import Configuration, Dict
from pybit import usdt_perpetual

class BybitClient():

    def __init__(self, config: str) -> None:
        self.config = Configuration(config)
        self.endpoint = "https://api.bybit.com"
        
        self.ticker: str | None = None
        self.ticker_info: Dict | None = None
        self.latest_symbol_info: Dict | None = None
        self.current_positions: List[Dict] | None = None
        self.symbols: List[Dict] | None = None
        
        self.auto_tp_status: bool = False
        self.auto_tp_data: Dict = {}
        
        #debug
        self.debug_log = []
            
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

        # Set data to None if wrong ticker so the UI class stop refreshing for nothing
        if not self.ticker:
            self.latest_symbol_info = None
            return
        
        data = Dict(msg).get("data")
        if data and data["symbol"] == self.ticker:
            self.latest_symbol_info = data
    
    
    def __handle_auto_tp_system(self, new_position: Dict):
        """ Will get the position info and shortcuts cmd and set the appropriate scale orders"""
        try:
            ticker = new_position["symbol"]
            ticker_info = next(info for info in self.symbols 
                                            if info["name"] == ticker)


            if (ticker == None) or (ticker_info == None) or (self.auto_tp_data == None):
                raise ValueError(f"Missing data to create autotp for {ticker}")
            
            number_of_orders = self.auto_tp_data["number_of_orders"]
            success, msg = self.__wrap_place_scale_orders(
                [new_position], 
                ticker, 
                ticker_info, 
                number_of_orders, 
                self.auto_tp_data["scale_from"], 
                self.auto_tp_data["scale_to"])
        
            if success == False:
                raise Exception(msg)
        except Exception as e:
            self.debug_log.append(str(e))
        
    def __handle_position_stream(self, msg):
        """ Called everytime we get into a position """
        raw_data: List[Dict] = Dict(msg).get("data")
        
        if raw_data == None:
            return 
        
        # filter out closed position (bybit call this event when we close a position, with a size of 0 lol)
        open_position_list = list(filter(lambda position: position["size"] > 0.0, raw_data))
        
        # save previous position
        previous_positions = self.current_positions if self.current_positions != None else []
        
        # set current positon to new positions
        self.current_positions = open_position_list
        
        # save new position by looking a prev ones
        new_position: Dict = {}
        for pos in self.current_positions:
            existing_pos = next((x for x in previous_positions if x["symbol"] == pos["symbol"]), None)
            if existing_pos == None:
                new_position = pos
                break

        # if atp is ON and new position was found
        if self.auto_tp_status == True and new_position != {}:
            self.__handle_auto_tp_system(new_position)
            
            
    def __init_listen_position(self):
        """ Call __handle_position_stream everytime we get into a position """
        self.websocket_auth_client.position_stream(self.__handle_position_stream)
        
    def __round_to_tick(self, value: float, tick_size: float) -> float:
        """ Round a value to the next tick """
        return math.ceil(value / tick_size) * tick_size
    
    def __ensure_http_result(self, http_result) -> Dict:
        """ Take HTTP response and throw appropriate error """
        # ret_code=0 and ext_code="" means create order success
        # ret_code=0 and ext_code!="" means create order success but some parameters were not set correctly
        # ret_code!=0 means create order fail
        # ext_code means please refer to Errors
        
        dict_http_result = Dict(http_result) 
        ret_code = int(dict_http_result.get("ret_code"))
        ext_code = dict_http_result.get("ext_code")
        
        if ret_code == 0 and ext_code != "":
            raise Exception(f"Wrong parameters, code :{ext_code}")
        if ret_code != 0:
            raise Exception(f"Bybit API error {ret_code} - {ext_code}")
        return dict_http_result
             
    def switch_ticker(self, new_ticker: str) -> Tuple[bool, str]:
        """ Get info on a ticker and set it as current """
        try:
            # Check if ticker exist
            ticker_info = next((info for info in self.symbols 
                                         if info["name"] == new_ticker), None)
            # If not, leave
            if ticker_info == None:
                raise ValueError(f"Ticker {new_ticker} not supported by Bybit")
            
            # Set new ticker & save ticker info
            self.ticker = new_ticker
            self.ticker_info = ticker_info
            
            # connect to price feed
            self.websocket_no_auth_client.instrument_info_stream(self.__handle_instrument_info_stream, self.ticker)
            
            return True, "OK"
        except Exception as e:
            self.ticker = None
            self.ticker_info = None
            return False, str(e)
         
    def __wrap_place_scale_orders(self, 
            current_positions: List[Dict], 
            ticker: str,
            ticker_info: Dict | None,
            number_of_orders: int,
            scale_from: float,
            scale_to: float) -> Tuple[bool, str]:
        """
            Wrapped to be able to call this func with different param from "self"
        """
        try:
            if current_positions == None:
                raise ValueError("You don't have any positon oppened")
            
            current_position_data = next(pos for pos in current_positions 
                                         if pos["symbol"] == ticker and pos["size"] > 0.0)
                        
            if current_position_data == None:
                raise ValueError("No current position found")
            
            if ticker_info == None:
                raise ValueError("Cannot find ticker info") 
        
            ticker_tick_size = float(ticker_info.get("price_filter")["tick_size"])
            ticker_price_scale = int(ticker_info.get("price_scale"))
            
            min_trad_quant = float(ticker_info["lot_size_filter"]["min_trading_qty"])
            max_trad_quant = float(ticker_info["lot_size_filter"]["post_only_max_trading_qty"])
            
            side = str(current_position_data.get("side"))
            entry_price = float(current_position_data.get("entry_price"))
            pos_size = float(current_position_data.get("size"))
            
            entry_to_percent = (entry_price / 100)
            
            from_value = entry_to_percent * scale_from
            from_price = entry_price + from_value if side == "Buy" else entry_price - from_value
            
            to_value = entry_to_percent * scale_to
            to_price = entry_price + to_value if side == "Buy" else entry_price - to_value
            
            steps = (to_price - from_price) / number_of_orders
            
            amount_per_order = pos_size / number_of_orders
            
            if amount_per_order < min_trad_quant:
                raise ValueError(f"Position size too small for the scaling, min order size : {min_trad_quant}")
            elif amount_per_order > max_trad_quant:
                raise ValueError(f"Scaling too small for the positon size : max pos size per limit order : {max_trad_quant}")
            
            acc = 0
            i = 1
            price_raw = 0
            http_result_msg: list[Dict] = []
            while i <= number_of_orders:
                price_raw = from_price + acc
                calculated_price = round(self.__round_to_tick(price_raw, ticker_tick_size), ticker_price_scale)
                result = self.http_client.place_active_order(
                    symbol=ticker,
                    side="Buy" if side == "Sell" else "Sell",
                    order_type="Limit",
                    qty=amount_per_order,
                    price=calculated_price,
                    time_in_force="PostOnly",
                    reduce_only=True,
                    close_on_trigger=False,
                    position_idx = 0
                )
                http_result_msg.append(self.__ensure_http_result(result))
                acc = acc + steps
                i = i + 1
            
            
            return True, http_result_msg[0]["ret_msg"]
        except Exception as e:
            print("Error in place_scale_orders", str(e))
            return False, str(e)
        
    def place_scale_orders(self, number_of_orders: int, scale_from: float, scale_to: float) -> Tuple[bool, str]:
        """ 
            Place multiple orders based on parameters 
            Use the wrapper func instead of using "self" bcs I want to use the code logic elswhere
        """
        return self.__wrap_place_scale_orders(self.current_positions, self.ticker, self.ticker_info, number_of_orders, scale_from, scale_to)
    
    def cancel_all_orders(self) -> Tuple[bool, str, int]:
        """ Will cancel all limit orders for current ticker """
        try:
            if self.ticker == None:
                raise ValueError("No ticker selected") 
            
            result = self.http_client.cancel_all_active_orders(symbol=self.ticker)
          
            dict_result = self.__ensure_http_result(result)
            
            if dict_result["result"] == None:
                return True, "OK", 0
            
            number_of_order_cancelled = len(dict_result["result"])
            
            return True, dict_result["ret_msg"], number_of_order_cancelled
        except Exception as e:
            print("Error in cancel_all_orders", str(e))
            return False, str(e), 0
        




