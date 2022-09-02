import sys
import discord
from typing import overload
from discord import app_commands
from discord.ext import commands
from persiandevbot.utils.logger import Logger

from ..bot import PDBot


# TODO:
#   - Add better error handling

class ErrorHandler(commands.Cog, name="ErrorHandler"):
    ERROR_MESSAGE_TEMPLATE = "```css\n#[ERROR]# {message}\n```"

    def __init__(self, bot: PDBot):
        self.__bot = bot
        self.__bot.tree.on_error = self.onAppCommandError
        self.__bot.on_command_error = self.onCommandError
        self.__bot.on_error = self.onError
        self.__logger = Logger("PDBot.ErrorHandler")

    async def onError(self, event: str, *args, **kwargs):
        self.__logger.error("onError (UNEXPECTED ERROR) "
                            f"EVENT(name=\"{event}\", args={args}, kwargs={kwargs}, error={sys.exc_info()[0:2]})")

    async def onAppCommandError(self, interaction: discord.Interaction, error):
        if isinstance(error, (app_commands.MissingRole, app_commands.MissingPermissions)):
            await interaction.response.send_message(content=self.ERROR_MESSAGE_TEMPLATE.replace("{message}","Shoma Role ya Permission mored niaz baray "
                                                            "ejray in command ra nadarid‼"), ephemeral=True)
        else:
            self.__logger.error(f"onAppCommandError (UNEXPECTED ERROR) "
                                f"INTERACTION(user={str(interaction.user)},"
                                f" channel={interaction.channel.name}, id={interaction.id},"
                                f" command={interaction.command.name}) ERROR({error})")
            if not interaction.is_expired():
                return await interaction.response.send_message(content=self.ERROR_MESSAGE_TEMPLATE.replace("{message}",
                                                                                                            "an unexpected error occurred‼"))
            await interaction.followup.send(content=self.ERROR_MESSAGE_TEMPLATE.replace("{message}",
                                                                                                "an unexpected error occurred‼"))

    async def onCommandError(self, ctx: commands.Context, exception: commands.CommandError):
            if isinstance(exception, commands.NotOwner):
                await ctx.send(self.ERROR_MESSAGE_TEMPLATE.replace("{message}", "Owner-only command, you are not"
                                                                                " the Owner of the bot."))
            else:
                self.__logger.error(f"onCommandError (UNEXPECTED ERROR) "
                                    f"CONTEXT(user={repr(ctx.author)},"
                                    f" channel={ctx.channel.name}, content=\"{ctx.message.content}\") ERROR({exception})")
                await ctx.send(content=self.ERROR_MESSAGE_TEMPLATE.replace("{message} "
                                                                           "an unexpected error occurred‼"))
    @classmethod
    @overload
    async def SendError(cls, interaction: discord.Interaction,
                        error_msg: str, *, ephemeral: bool = True, followup: bool = False):
        ...

    @classmethod
    @overload
    async def SendError(cls, message: discord.Message, error_msg: str, ephemeral: bool = True):
        ...

    @classmethod
    @overload
    async def SendError(cls, channel: discord.abc.Messageable, error_msg: str):
        ...

    @classmethod
    async def SendError(cls, x, error_msg: str, *, ephemeral: bool = True, followup: bool = False) -> None:
        message = cls.ERROR_MESSAGE_TEMPLATE.replace("{message}", error_msg)
        if isinstance(x, discord.Interaction):
            if followup:
                return await x.followup.send(content=message, ephemeral=ephemeral)
            if x.is_expired():
                return await cls.SendError(x, error_msg, ephemeral=ephemeral, followup=True)
            return await x.response.send_message(message, ephemeral=ephemeral)
        elif isinstance(x, discord.Message):
            await x.reply(message)
            return
        elif isinstance(x, discord.abc.Messageable):
            await x.send(message)
            return

        raise TypeError(f"Expected type [discord.Interaction, discord.Message, discord.abc.Messageable] "
                        f"got type \"{type(x)}\" instead!")


async def setup(bot: PDBot):
    if not bot.config.Features.ERROR_HANDLER:
        return bot.logger.info("Extension ERROR_HANDLER have been set to false in config, ignoring loading.")
    await bot.add_cog(ErrorHandler(bot))
