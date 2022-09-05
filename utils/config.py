import logging
import os
import json
from typing import Union

from utils.logger import Logger


class ConfigLoader:
    """
    ConfigLoader loads config from the given json file and adds root keys and 1-level down subkeys
    as atters of it self.
    **Bot Token is loaded from OS Environment (os.environ) with the name of "DISCORD_API_SECRET"**

    param:
        - path : os.PathLike | str | None -> path to the .json config file
    """
    class __CONTAINER:
        pass

    __instance: object = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is not None:
            return cls.__instance
        return super(cls.__class__, cls).__new__(cls)

    def __init__(self, path: os.PathLike | str | None = None):
        if ConfigLoader.__instance is not None and path is None:
            return
        self.__path = path
        self.__logger = Logger("PDBot.ConfigLoader", logging.INFO)
        # Loading from config.json file
        with open(path, "r") as cfgFile:
            self.__data: dict = json.load(cfgFile)
            self.__logger.info(f"Loaded Config from \"{path}\"!")
        for root, subs in self.__data.items():
            if isinstance(subs, dict):
                container = self.__CONTAINER()
                for k, v in subs.items():
                    container.__setattr__(str(k), v)
                self.__setattr__(str(root), container)
            else:
                self.__setattr__(str(root), self.__data[root])
        self.__setattr__("DISCORD_API_SECRET", os.environ["DISCORD_API_SECRET"])
        self.__setattr__("REPORT_WEBHOOK_URL", os.environ["REPORT_WEBHOOK_URL"])
        self.__logger.info("Loaded token from environ!")

    def update(self, new_data: dict):
        with open("config.json", 'r') as cfgFile:
            json.dump(new_data, cfgFile)
            self.__logger.info(f"Updated configuration file (\"{self.__path}\")!")

    @property
    def data(self) -> dict:
        return self.__data
