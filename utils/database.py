import os
import aiosqlite

"""
This utility module is made for support with SQLite databases in an asynchronous environment.
although because the bot is going the be running in replit, all parts of the bot that reference this utility module are 
commented out.
"""

class SqlDatabaseHandler:
    def __init__(self, path: os.PathLike | str):
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
