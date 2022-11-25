
from textual.widget import Widget
from rich.console import RenderableType
from rich.align import Align
from rich.panel import Panel

from json_loader import JSON_CONFIG


class ShortCutSideBar(Widget):
    """ Display shortcuts sidebar """

    def __init__(self, *, name: str | None = None, shortcut_cfg: JSON_CONFIG, height: int | None = None) -> None:
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
        
def remove_space_and_split(string: str) -> list[str]:
    return " ".join(string.split()).split(" ")