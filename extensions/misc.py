import logging

import discord
from discord.ext import commands
from utils.logger import Logger
from extensions.error_handler import ErrorHandler
from bot import PDBot


class Misc(commands.Cog):
    def __init__(self, bot: PDBot):
        self.__bot = bot
        self.__logger = Logger('PDBot.Misc')

    async def cog_load(self) -> None:
        self.__logger.info("Extension Loaded!")

    async def cog_unload(self) -> None:
        self.__logger.info("Extension Unloaded!")

    @discord.app_commands.command(name="ping",
                                  description="Pong??")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=f"Pong🏓\nWEBSOCKET: {round(self.__bot.latency * 1000)}", ephemeral=True)

    @discord.app_commands.command(name="sync",
                                  description="Syncs the global command tree to the super guild (OWNER-ONLY)")
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if interaction.user.id != self.__bot.owner_id:
            return await ErrorHandler.SendError(interaction, "OWNER ONLY COMMAND. You are not the owner of the bot!", followup=True)
        self.__bot.tree.copy_global_to(guild=self.__bot.superGuild)
        await self.__bot.tree.sync(guild=self.__bot.superGuild)
        await interaction.followup.send("Synced✅", ephemeral=True)


async def setup(bot: PDBot):
    if not bot.config.Features.MISC:
        return bot.logger.info("Extension MISC have been set to false in config, ignoring loading.")
    await bot.add_cog(Misc(bot), guild=bot.superGuild)
