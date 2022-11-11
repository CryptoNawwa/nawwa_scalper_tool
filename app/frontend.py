import os

from textual.app import App
from rich.panel import Panel
from textual.widgets import Header, Footer
from textual_inputs import TextInput
from rich.text import Text
from textual import events
from ck_widgets.widgets import ListViewUo
from textual.widget import Widget, Reactive
from rich.console import RenderableType
from rich.align import Align

from bybit.bybit import Bybit
from exchange.exchange import Exchange
from exchange.positions_info import Position
from exchange.auto_take_profit_data import AutoTakeProfitScaleData, AutoTakeProfitSingleTpData
from frontend_tools import remove_space_and_split
from config import Configuration

from datetime import datetime
from typing import List, Tuple, cast

SHORTCUT_PATH = os.path.join(os.path.dirname(__file__), 'shortcuts/shortcuts.json')
DEFAULT_TERM_TITLE = "Terminal [white]-[/white] [No ticker selected]"
SHORTCUTS_SIDEBAR_SIZE = 80


class ShortCutSideBar(Widget):
    """Display shortcuts sidebar """

    def __init__(self, *, name: str | None = None, shortcut_cfg: Configuration, height: int | None = None) -> None:
        super().__init__(name=name)
        self.shortcuts_cfg = shortcut_cfg
        self.log(str(self.shortcuts_cfg.data))

    def render(self) -> RenderableType:
        self.shortcuts = ""
        for f in self.shortcuts_cfg.data:
            self.shortcuts += f"[bold magenta]{str(f)}[/] --> [blue]{self.shortcuts_cfg.data[f]}[/]\n"

        return Panel(
            Align.left(self.shortcuts),
            title=f"[bold blue]Shortcuts[/]",
            border_style="blue",
        )


class Frontend(App):
    def __init__(self, exchange_client: Exchange, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Set shortcut cfg handler
        self.shortcuts_cfg = Configuration(SHORTCUT_PATH, live=True)

        # Chekc if client inherit Exchange
        is_instance = issubclass(type(exchange_client), Exchange)
        self.client: Exchange | None = exchange_client if is_instance else None

        self.display_title = 'Nawwa\'s Scalping Tool'

    show_shortcuts_bar = Reactive(False)

    async def on_load(self, event: events.Load) -> None:
        """ Register keybindings """

        await self.bind("enter", "submit", "Send command")
        await self.bind("l", "toggle_shortcuts_sidebar", "Shortcuts")
        await self.bind("q", "quit", "Quit")
        await self.bind("ctrl+q", "quit", show=False)

    async def on_mount(self) -> None:
        if (self.client is None):
            raise Exception("Exchange client is None, init the frontend with a proper client")

        # Setup widgets
        self.terminal_cmd = TextInput(
            name="cmd",
            title=DEFAULT_TERM_TITLE,
            placeholder="> "
        )
        self.history_view = ListViewUo([])
        self.footer = Footer()
        self.header = Header(style="white")
        self.shortcuts_sidebar = ShortCutSideBar(name="Shortcuts", shortcut_cfg=self.shortcuts_cfg)
        self.shortcuts_sidebar.layout_offset_x = -SHORTCUTS_SIDEBAR_SIZE

        # add widgets to dock
        await self.view.dock(self.header, edge="top")
        await self.view.dock(self.footer, edge="bottom")
        await self.view.dock(self.terminal_cmd, edge='top', size=4)
        await self.view.dock(self.history_view)
        await self.view.dock(self.shortcuts_sidebar, edge="left", size=SHORTCUTS_SIDEBAR_SIZE, z=1)

        # Fetch ticker data to update terminal UI
        self.set_interval(1, self._interval_check_bybit_updates)
        self.refresh()

    def watch_show_shortcuts_bar(self, show_shortcuts_bar: bool) -> None:
        """Show/hide shortcuts sidebar"""

        self.shortcuts_sidebar.animate("layout_offset_x", 0 if show_shortcuts_bar else -SHORTCUTS_SIDEBAR_SIZE)

    def action_toggle_shortcuts_sidebar(self) -> None:
        """Trigger show/hide mirror sidebar"""

        if not self.show_shortcuts_bar: False
        self.show_shortcuts_bar = not self.show_shortcuts_bar

    def _change_terminal_title(self, ticker: str | None, price: str | None, positions: Position | None) -> None:
        """ Change the terminal title based on arg and refresh screen if necessary  """
        previous_title = self.terminal_cmd.title

        final_title = "Terminal [white]-[/white] "
        ticker_text = f"[gold1]{ticker}[/gold1] [white]-[/white]"
        price_text = f"[gold1]${price}[/gold1]"
        if price and ticker and positions:
            side = str(positions["side"])
            size = float(positions["size"])
            final_title += f"{ticker_text} {price_text} [white]-[/white] "
            final_title += (f"[dark_turquoise]{size}[/dark_turquoise]"
                            if side == "Buy" else f"[deep_pink3]{size}[/deep_pink3]")
        elif price and ticker and positions is None:
            final_title += f"{ticker_text} {price_text}"
        elif ticker and not price and not positions:
            final_title += f"{ticker_text}"
        else:
            final_title = DEFAULT_TERM_TITLE

        self.terminal_cmd.title = final_title
        if self.terminal_cmd.title != previous_title:
            self.terminal_cmd.refresh()

    def _handle_terminal_title_info(self):
        """ Called by interval func, will get data to update the terminal title """
        latest_symbol_info = self.client.get_latest_price_info_for_active_symbol()
        # If no ticker info, reset text input and return
        if not latest_symbol_info:
            self._change_terminal_title(None, None, None)
            return

        # Get symbol basic info
        symbol_info = latest_symbol_info
        symbol = symbol_info.get('symbol')
        last_price = str(symbol_info.get('last_price'))

        try:
            # Get position data (if any)
            current_position = self.client.get_current_positions()
            current_position_data = next((pos for pos in current_position
                                          if pos.get("symbol") == symbol), None)

            # Changer terminal title based on data
            self._change_terminal_title(symbol, last_price, current_position_data)
        except Exception as e:
            self._change_terminal_title(symbol, last_price, None)

    def _interval_check_bybit_updates(self):
        """ Look in bybit class if we got some new data to print """

        # If no bybit client, return
        if not self.client:
            return

        debug_log = self.client.get_error_log(True)
        # Print client debug array in file
        if len(debug_log) > 0:
            for x in debug_log:
                self.log(x)

        # Update terminal title #
        self._handle_terminal_title_info()

    def _extract_data_from_scale_cmd(self, cmd_list: List[str]) -> Tuple[int, float, float]:
        """ Helper to extract data from the scale cmd typed by user"""

        if len(cmd_list) != 4:
            raise ValueError("Wrong scale syntax")

        number_of_orders = int(cmd_list[1])
        scale_from = float(cmd_list[2])
        scale_to = float(cmd_list[3])

        if scale_from <= 0.0 or scale_to <= 0.0 or scale_from >= scale_to or number_of_orders <= 0:
            raise ValueError("Wrong data for scale order")
        return number_of_orders, scale_from, scale_to

    def _extract_data_from_tp_cmd(self, cmd_list: List[str]) -> float:
        """ Helper to extract data from the tp cmd typed by user"""

        if len(cmd_list) != 2:
            raise ValueError("Wrong tp syntax")

        percent_away = float(cmd_list[1])

        if percent_away <= 0.0:
            raise ValueError("Wrong data for tp command")
        return percent_away

    def _get_shortcut_from_cfg(self, shortcut: str) -> str | None:
        return self.shortcuts_cfg.data.get(shortcut, None)

    async def add_text_to_history_list(self, cmd: str, result: str | None) -> None:
        """Add text to the history list on the UI"""

        # Build text
        time = datetime.now().strftime("%H:%M:%S")
        actual_result = result if result else "Command not found"
        text = Text.assemble("> ", (cmd, "bold magenta"), " -> ", (actual_result, "blue"), " - ", (time),
                             no_wrap=True, justify="left")

        # Add to screen
        await self.history_view.add_widget(text, index=0)

    async def cmd_select_ticker(self, raw_cmd, cmd_list: List[str]) -> None:
        """ Ticker command ie ticker ethusdt"""
        try:
            if len(cmd_list) != 2:
                raise ValueError("Wrong command syntax")

            new_ticker = str.upper(cmd_list[1])

            if not new_ticker.find("USDT"):
                raise ValueError("Only accept USDT ticker")

            # Call bybit client to switch ticker
            success, msg = self.client.terminal_cmd_switch_active_symbol(new_ticker)

            if success is True:
                await self.add_text_to_history_list(raw_cmd, f"Successfully switched ticker to {new_ticker}")
            else:
                await self.add_text_to_history_list(raw_cmd, msg)
        except Exception as e:
            self.log(f'Error in cmd_select_ticker : {str(e)}')
            await self.add_text_to_history_list(raw_cmd, str(e))

    async def cmd_cancel_orders(self, raw_cmd, cmd_list: List[str]) -> None:
        """ Cancel command ie cancel all"""
        try:
            if len(cmd_list) != 2:
                raise ValueError("Wrong syntax")

            to_cancel = cmd_list[1]

            success: bool
            msg: str
            nb_of_order: int
            match str.upper(to_cancel):
                case "ALL":
                    success, msg, nb_of_order = self.client.terminal_cmd_cancel_all_orders()
                case _:
                    raise ValueError(f"No command matching {to_cancel}")

            if success is True:
                await self.add_text_to_history_list(raw_cmd, (f"{nb_of_order} orders successfully cancelled"
                                                              if nb_of_order > 0 else "No limit orders to cancel"))
            else:
                await self.add_text_to_history_list(raw_cmd, msg)
        except Exception as e:
            self.log(f'Error in cmd_cancel_orders : {str(e)}')
            await self.add_text_to_history_list(raw_cmd, str(e))

    async def cmd_auto_tp(self, raw_cmd, cmd_list: List[str]) -> None:
        """ AutoTakeProfit, will automatically place tp if enter a pos"""
        try:
            if len(cmd_list) < 2:
                raise ValueError("Wrong syntax")

            user_input_atp_action = str.upper(cmd_list[1])

            # Guards user input action
            if user_input_atp_action == "ON" and len(cmd_list) < 3:
                raise ValueError("Cannot set autotp to ON without a following shortcut")
            elif user_input_atp_action == "OFF":
                self.client.auto_tp_data = None
                await self.add_text_to_history_list(raw_cmd, f"Auto take profit is now {user_input_atp_action}")
                return
            elif user_input_atp_action == "STATUS" or user_input_atp_action == "ST":
                status = "ON" if self.client.auto_tp_data is not None else "OFF"
                await self.add_text_to_history_list(raw_cmd, f"Auto take profit status is [{status}]")
                return

            user_input_shortcut = cmd_list[2]

            # get user input and find the shortcut from cfg 
            shortcut_found = self._get_shortcut_from_cfg(user_input_shortcut)

            if shortcut_found is None:
                raise ValueError(f"Cannot find shortcut {user_input_shortcut}")

            await self.add_text_to_history_list("shortcut found ", shortcut_found)
            # transform shortcut found to list
            atp_command_list = remove_space_and_split(shortcut_found)

            is_single_tp_shortcut = atp_command_list[0] == 'tp'
            is_scale_tp_shortcut = atp_command_list[0] == "scale" or atp_command_list[0] == "s"

            # ensure the shortcut is a scale or tp shortcut
            if is_single_tp_shortcut is False and is_scale_tp_shortcut is False:
                raise ValueError(f"Wrong shortcut, please only set scale or tp shortcut for atp command")
        

          
            if is_scale_tp_shortcut:
                # extract data from shortcut
                number_of_orders, scale_from, scale_to = self._extract_data_from_scale_cmd(atp_command_list)

                auto_take_profit_scale_data = cast(AutoTakeProfitScaleData, {
                    "number_of_order": 0,
                    "scale_from": 0.0,
                    "scale_to": 0.0,
                })

                # Set data into bybit client
                auto_take_profit_scale_data["number_of_orders"] = number_of_orders
                auto_take_profit_scale_data["scale_from"] = scale_from
                auto_take_profit_scale_data["scale_to"] = scale_to

                self.client.auto_tp_data = auto_take_profit_scale_data

            elif is_single_tp_shortcut:
                # extract data from shortcut
                percent_away = self._extract_data_from_tp_cmd(atp_command_list)

                auto_take_profit_single_tp_data = cast(AutoTakeProfitSingleTpData, {
                    "percent_away": 0.0,
                })
                auto_take_profit_single_tp_data["percent_away"] = percent_away

                self.client.auto_tp_data = auto_take_profit_single_tp_data

            if user_input_atp_action == "ON":
                await self.add_text_to_history_list(raw_cmd,
                  f"Auto take profit is now [{user_input_atp_action}] with shortcut {user_input_shortcut}")
            elif user_input_atp_action == "UPDATE" or user_input_atp_action == "UP":
                await self.add_text_to_history_list(raw_cmd,
                    f"Auto take profit was updated to use shortcut {user_input_shortcut}")
        except Exception as e:
            self.log(f'Error in cmd_auto_tp : {str(e)}')
            await self.add_text_to_history_list(raw_cmd, str(e))

    async def cmd_scale_limit_order(self, raw_cmd, cmd_list: List[str]) -> None:
        """ Scale command .ie scale 10 0.1 0.4 """
        try:

            active_symbol = self.client.get_active_symbol()

            if active_symbol is None:
                raise ValueError("No active symbol")

            number_of_orders, scale_from, scale_to = self._extract_data_from_scale_cmd(cmd_list)

            success, msg = self.client.terminal_cmd_set_scale_orders({
                "number_of_orders": number_of_orders,
                "scale_from": scale_from,
                "scale_to": scale_to
            })

            if success is True:
                await self.add_text_to_history_list(raw_cmd,
                                                    f"{number_of_orders} limit orders placed from {scale_from}% to {scale_to}% ")
            else:
                await self.add_text_to_history_list(raw_cmd, msg)
        except Exception as e:
            self.log(f'Error in cmd_scale_limit_order : {str(e)}')
            await self.add_text_to_history_list(raw_cmd, str(e))

    async def cmd_tp_limit_order(self, raw_cmd, cmd_list: List[str]) -> None:
        """ Take profit single order cmd ie. tp 0.4 """
        try:

            active_symbol = self.client.get_active_symbol()

            if active_symbol is None:
                raise ValueError("No active symbol")

            percent_away = self._extract_data_from_tp_cmd(cmd_list)

            success, msg = self.client.terminal_cmd_send_single_tp_order({"percent_away": percent_away})

            if success is True:
                await self.add_text_to_history_list(raw_cmd,
                                                    f"Take profit limit order placed")
            else:
                await self.add_text_to_history_list(raw_cmd, msg)
        except Exception as e:
            self.log(f'Error in cmd_tp_limit_order : {str(e)}')
            await self.add_text_to_history_list(raw_cmd, str(e))

    async def cmd_manage_shortcuts(self, raw_cmd: str, cmd_list: List[str]) -> None:
        if len(cmd_list) < 3:
            raise ValueError("Wrong syntax, ex: shortcut add/del/up btc ticker btcusdt")

        shortcut_action = str.upper(cmd_list[1])
        shortcut_name = cmd_list[2]

        match shortcut_action:
            case "ADD" | "UPDATE" | "UP":
                shortcut_value = " ".join(cmd_list[3:])
                success = self.shortcuts_cfg.add(shortcut_name, shortcut_value)
                if success:
                    await self.add_text_to_history_list(raw_cmd, f"Shortcut {shortcut_name} is now {shortcut_value}")
                    return
            case "DEL":
                success = self.shortcuts_cfg.delete(shortcut_name)
                if success:
                    await self.add_text_to_history_list(raw_cmd, f"Shortcut {shortcut_name} was deleted")
                    return
            case _:
                await self.add_text_to_history_list(raw_cmd, f"Shortcut action {shortcut_action} not supported")
                return

        await self.add_text_to_history_list(raw_cmd, f"Could not perform {shortcut_action} on {shortcut_name} ")

    async def execute_terminal_cmd(self, raw_cmd, cmd_list: List[str]) -> None:
        """ Will try to execute cmd """
        first_command = cmd_list[0]
        match first_command:
            case "ticker" | "t":
                await self.cmd_select_ticker(raw_cmd, cmd_list)
            case "scale" | "s":
                await self.cmd_scale_limit_order(raw_cmd, cmd_list)
            case "tp":
                await self.cmd_tp_limit_order(raw_cmd, cmd_list)
            case "cancel" | "c":
                await self.cmd_cancel_orders(raw_cmd, cmd_list)
            case "autotp" | "atp":
                await self.cmd_auto_tp(raw_cmd, cmd_list)
            case "shortcut" | "sc":
                await self.cmd_manage_shortcuts(raw_cmd, cmd_list)
            case "quit":
                await self.app.action_quit()
            case _:
                await self.add_text_to_history_list(first_command, None)

    async def action_submit(self) -> None:
        """ Command input submit event """
        with self.console.status("Talking with Bybit.."):
            # set cmd & shortcut
            cmd = self.terminal_cmd.value
            shortcut = self._get_shortcut_from_cfg(cmd)

            # use cmd or shortcut
            to_execute = shortcut if shortcut is not None else cmd

            self.log(f'cmd to execute "{to_execute}"')

            # trim space & split cmd by space & send it
            to_execute_list = remove_space_and_split(to_execute)

            await self.execute_terminal_cmd(to_execute, to_execute_list)

            self.terminal_cmd.value = ""
            self.terminal_cmd.refresh()


def main():
    Frontend.run(exchange_client=Bybit(), title="Nawwa's Scalping Tool", log="scalping_tool.log")


if __name__ == '__main__':
    main()
