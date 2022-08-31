import asyncio
import os
# import sqlite3
import aiosqlite


class DatabaseHandler:
    def __init__(self, path: os.PathLike[str] | str):
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

    def __del__(self):
        asyncio.run(self.__connection.commit())
        asyncio.run(self.__cursor.close())
        asyncio.run(self.__connection.close())


