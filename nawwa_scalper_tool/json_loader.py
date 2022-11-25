from __future__ import annotations
import json


class Dict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__  # type: ignore
    __delattr__ = dict.__delitem__  # type: ignore


class JSON_CONFIG(object):
    """JSON configuration object"""

    def __init__(self, file_path: str, live=True) -> None:
        self.path = file_path
        with open(self.path, 'r') as f:
            self.data = Dict(json.load(f))
        self.live = live

    def add(self, key: str, value: str) -> bool:
        try:
            self.data[key] = value
            if self.live: self.__update()
            return True
        except:
            return False

    def delete(self, key: str) -> bool:
        try:
            del self.data[key]
            if self.live: self.__update()
            return True
        except:
            return False

    def __update(self) -> None:
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def write(self):
        self.__update()