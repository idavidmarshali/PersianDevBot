import asyncio
import os
import aiosqlite
from typing import Union


class DatabaseHandler:
    def __init__(self, path: Union[os.PathLike, str]):
        self.__path = path
        self.__connection: aiosqlite.Connection = ...
        self.__cursor: aiosqlite.Cursor = ...

    async def init(self) -> None:
        self.__connection = await aiosqlite.connect(self.__path)
        self.__cursor = await self.__connection.cursor()

    async def kill(self) -> None:
        await self.__connection.commit()
        await self.__cursor.close()
        await self.__connection.close()

    @property
    def connection(self) -> aiosqlite.Connection:
        return self.__connection

    @property
    def cursor(self) -> aiosqlite.Cursor:
        return self.__cursor



