import logging
from typing import Union


class Logger(logging.Logger):
    __formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", '%Y-%m-%d %H:%M:%S', style="{")
    DEFAULT_LEVEL = logging.ERROR

    def __init__(self, name: str, level: Union[int, str] = DEFAULT_LEVEL):
        super().__init__(name, level)
        self.handler = logging.StreamHandler()
        self.handler.setLevel(level)
        self.handler.setFormatter(Logger.__formatter)
        self.addHandler(self.handler)
