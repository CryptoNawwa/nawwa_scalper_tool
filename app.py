from datetime import datetime
from typing import List
from textual.app import App
from rich.panel import Panel
from textual.widgets import Header, Footer
from textual_inputs import TextInput
from rich.text import Text
from textual import events
from bybit_client import BybitClient
from config import ConfigUpdateForm, Configuration, Dict

from ck_widgets_lv import ListViewUo
from textual.widget import Widget, Reactive
from rich.console import RenderableType
from rich.align import Align

import argparse
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'data/conf.json')
SHORTCUT_PATH = os.path.join(os.path.dirname(__file__), 'data/shortcuts.json')
DEFAULT_TERM_TITLE = "Terminal [white]-[/white] [No ticker selected]"
SHORTCUTS_SIDEBAR_SIZE = 80

class ShortCutSideBar(Widget):
    """Display shortcuts """

    def __init__(self, *,  name: str | None = None, height: int | None = None) -> None:
        super().__init__(name=name)
        self.config = Configuration(SHORTCUT_PATH, live=False)
        self.log(str(self.config.data))

    def render(self) -> RenderableType:
        self.shortcuts = ""
        for f in self.config.data:
            self.shortcuts +=  f"[bold magenta]{str(f)}[/] --> [blue]{self.config.data[f]}[/]\n"
            
        return Panel(
            Align.left(self.shortcuts),
            title=f"[bold blue]Shortcuts[/]",
            border_style="blue",
        )

class BybitScalperFront(App):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.shortcuts = Configuration(SHORTCUT_PATH, live=False)
        self.client = BybitClient(CONFIG_PATH)
        self.display_title = 'ScalBit'

    async def on_load(self, event: events.Load) -> None:
        """Register keybindings + dummy keybindings for widget events"""

        await self.bind("enter", "submit", "Send command")
        await self.bind("m", "toggle_shortcuts_sidebar", "Shortcuts")
        await self.bind("q", "quit", "Quit")
        await self.bind("ctrl+q", "quit", show=False)
        
    show_shortcuts_bar = Reactive(False)

    async def on_mount(self) -> None:
        # Setup widgets
        self.terminal_cmd = TextInput(
            name="cmd",
            title=DEFAULT_TERM_TITLE,
            placeholder="> "
        )
        self.history_view = ListViewUo([])
        self.footer = Footer()
        self.header = Header(style="white")
        self.shortcuts_sidebar = ShortCutSideBar(name="Shortcuts")
        self.shortcuts_sidebar.layout_offset_x = -SHORTCUTS_SIDEBAR_SIZE

        # add widgets to dock
        await self.view.dock(self.header, edge="top")
        await self.view.dock(self.footer, edge="bottom")
        await self.view.dock(self.terminal_cmd, edge='top', size=4)
        await self.view.dock(self.history_view)
        await self.view.dock(self.shortcuts_sidebar, edge="left", size=SHORTCUTS_SIDEBAR_SIZE, z=1)
        
        # Fetch ticker data to update terminal UI
        self.set_interval(1, self.fetch_ticker_data)
        self.refresh()
    
    def watch_show_shortcuts_bar(self, show_shortcuts_bar: bool) -> None:
        """Show/hide shortcuts sidebar"""

        self.shortcuts_sidebar.animate("layout_offset_x", 0 if show_shortcuts_bar else -SHORTCUTS_SIDEBAR_SIZE)

    def action_toggle_shortcuts_sidebar(self) -> None:
        """Trigger show/hide mirror sidebar"""

        if not self.show_shortcuts_bar: False
        self.show_shortcuts_bar = not self.show_shortcuts_bar
    
    def change_terminal_title(self, ticker: str | None, price: str | None, positions: Dict | None) -> None:
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
        elif price and ticker and positions == None:
            final_title += f"{ticker_text} {price_text}"
        elif ticker and not price and not positions:
            final_title += f"{ticker_text}"
        else:
            final_title = DEFAULT_TERM_TITLE
            
        self.terminal_cmd.title = final_title
        if self.terminal_cmd.title != previous_title:
            self.terminal_cmd.refresh()
        
    def fetch_ticker_data(self):
        """ Fetch ticker data from Bybit client """
        if not self.client or not self.client.latest_symbol_info:
            self.change_terminal_title(None, None, None)
            return
    
        # Get symbol basic info
        symbol_info = self.client.latest_symbol_info
        symbol = str(symbol_info.get('symbol'))
        last_price = str(symbol_info.get('last_price'))

        try:
            # Get positon data (if any)
            current_position_data: Dict | None = None
            if self.client.current_positions:
                current_position_data = next(pos for pos in self.client.current_positions 
                                        if pos["symbol"] == symbol and pos["size"] > 0.0)
            self.change_terminal_title(symbol, last_price, current_position_data)
        except Exception as e:
            self.change_terminal_title(symbol, last_price, None)
     
      
            
            
 
          
    def get_shortcut_from_cmd(self, cmd: str) -> str | None:
        for f in self.shortcuts.data:
            if (str(f) == cmd):
                return self.shortcuts.data[f]
        return None
    
    async def add_text_to_history_list(self, cmd: str, result: str | None) -> None:
        """Add text to history list"""
        
        # Build text
        time = datetime.now().strftime("%H:%M:%S")
        acutal_result = result if result else "Command not found"
        text = Text.assemble(("> "), (cmd, "bold magenta"), (" -> "), (acutal_result, "blue"), (" - "), (time), no_wrap=True, justify="left")
        
        # Add to screen
        await self.history_view.add_widget(text, index=0)
    
    async def cmd_select_ticker(self, raw_cmd, cmd_list:  List[str]) -> None:
        """ Ticker command ie ticker ethusdt"""
        try:
            if len(cmd_list) != 2:
                raise ValueError("Wrong syntax")
            
            new_ticker = str.upper(cmd_list[1])

            if not new_ticker.find("USDT"):
                raise ValueError("Only accept USDT")
            
            # Call bybit client
            success, msg = self.client.switch_ticker(new_ticker)
            
            self.log(f'switch_ticker for "{new_ticker}" -> {success}')
        
            if success == True:
                await self.add_text_to_history_list(raw_cmd, f"Successfully switched ticker to {new_ticker}")
            else:
                await self.add_text_to_history_list(raw_cmd, msg)
        except Exception as e:
            self.log(f'Error in cmd_select_ticker : {e}')
            await self.add_text_to_history_list(raw_cmd, f"Ticker not found")
            
    async def cmd_scale_exit_order(self, raw_cmd, cmd_list:  List[str]) -> None:
        """ Scale command .ie scale 10 0.1 0.4 """
        try :
            if len(cmd_list) != 4:
                raise ValueError("Wrong scale syntax")
            if self.client.ticker == None:
                raise ValueError("Select a ticker first")
        
            number_of_orders = int(cmd_list[1])
            scale_from = float(cmd_list[2])
            scale_to = float(cmd_list[3])
            
            if scale_from <= 0.0 or scale_to <= 0.0 or scale_from >= scale_to or number_of_orders <= 0:
                raise ValueError("Wrong data for scale order")
        
            success, msg = self.client.place_scale_orders(number_of_orders, scale_from, scale_to)
            
            if success == True:
                await self.add_text_to_history_list(raw_cmd, f"{number_of_orders} limit orders placed from {scale_from}% to {scale_to}% ")
            else:
                await self.add_text_to_history_list(raw_cmd, msg)
        except Exception as e:
            self.log(f'Error in cmd_scale_exit_order : {str(e)}')
            await self.add_text_to_history_list(raw_cmd, str(e))
        
        
    
    async def execute_terminal_cmd(self, raw_cmd, cmd_list: List[str]) -> None:
        """ Will try to execute cmd """
        first_command = cmd_list[0]
        match first_command:
            case "ticker" | "t":
                await self.cmd_select_ticker(raw_cmd, cmd_list)
            case "scale" | "sc":
                await self.cmd_scale_exit_order(raw_cmd, cmd_list)
            case _:
                await self.add_text_to_history_list(first_command, None)
                           
    async def action_submit(self) -> None:
        """Command input submit event"""
        with self.console.status("Talking with Bybit.."):
            # set cmd & shortcut
            cmd = self.terminal_cmd.value
            shortcut = self.get_shortcut_from_cmd(cmd)
            
            # use cmd or shortcut
            to_execute = shortcut if shortcut != None else cmd
            self.log(f'cmd to execute "{to_execute}"')
            
            # split cmd by space & send it
            to_execute_list = " ".join(to_execute.split()).split(" ")
            await self.execute_terminal_cmd(to_execute, to_execute_list)
            
            self.terminal_cmd.value = ""
            self.terminal_cmd.refresh()

    

def parse() -> argparse.Namespace:
    """Argument parser; options for launching configuration editor or enabling logs"""

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="configure settings", action="store_true")
    return parser.parse_args()

def main():
    args = parse()
    if args.config:
        ConfigUpdateForm.run(title='Bybit Scalping Tool cfg', path=CONFIG_PATH, log="textual.log")
    else:
        BybitScalperFront.run(title="Bybit Scalping Tool", log="textual.log")

if __name__ == '__main__':
    main()