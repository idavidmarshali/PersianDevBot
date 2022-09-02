import discord
from discord.ext import commands
from .utils.logger import Logger
from .utils.config import ConfigLoader



class PDBot(commands.Bot):
    def __init__(self, prefix: str | list[str], intents: discord.Intents, config: ConfigLoader, extensions: list[str] = []):

        self.__extensions = extensions
        self.__config = config
        self.__logger = Logger("PDBot")
        self.__superGuild = discord.Object(id=self.__config.Bot.SUPER_SV_ID)
        super().__init__(command_prefix=prefix, intents=intents)

    @property
    def logger(self) -> Logger:
        return self.__logger

    @property
    def config(self) -> ConfigLoader:
        return self.__config

    @property
    def superGuild(self) -> discord.Object:
        return self.__superGuild

    async def setup_hook(self) -> None:
        for extension in self.__extensions:
            await self.load_extension(extension)

        self.tree.copy_global_to(guild=self.__superGuild)
        await self.tree.sync(guild=self.__superGuild)

    async def on_ready(self):
        self.__logger.info(f"BOT is logged in as [{self.user.name}#{self.user.discriminator}]!")
        self.__superGuild = self.get_guild(self.__config.Bot.SUPER_SV_ID)
        if self.__superGuild is None:
            self.__superGuild = await self.fetch_guild(self.__config.Bot.SUPER_SV_ID)
        self.__logger.info(f"SuperGuild Received: {self.__superGuild.name}({self.__superGuild.id})")

        app_info = await self.application_info()
        self.owner_id = app_info.owner.id
