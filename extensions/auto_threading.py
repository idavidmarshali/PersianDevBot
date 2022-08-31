import logging
import typing

import discord
from discord.ext import commands

from typing import overload
from bot import PDBot
from utils.logger import Logger
from utils.database import DatabaseHandler
from extensions.error_handler import ErrorHandler

# TODO:
#   - Refactor the code if needed
#   - Optimize the code if needed


class _AutoThreadingChannel:
    def __init__(self, channel: discord.TextChannel, creation_text: str):
        self.channel = channel
        self.creation_text = creation_text

    @property
    def discord_id(self) -> int:
        return self.channel.id


class _AutoThreadingCache:
    def __init__(self):
        self.__channels: list[_AutoThreadingChannel] = []

    def __contains__(self, item):
        __channel_id: int = item

        if isinstance(item, discord.TextChannel):
            __channel_id = item.id

        for channel in self.__channels:
            if channel.discord_id == __channel_id:
                return True
        return False

    def __iter__(self):
        return iter(self.__channels)

    def add(self, channel: discord.TextChannel, creation_text: str):
        self.__channels.append(_AutoThreadingChannel(channel, creation_text))

    @overload
    def get(self, _id: int) -> _AutoThreadingChannel | None:
        ...

    @overload
    def get(self, channel: discord.TextChannel) -> _AutoThreadingChannel | None:
        ...

    def get(self, x):
        __channel_id: int = x.id if isinstance(x, discord.TextChannel) else x
        for channel in self.__channels:
            if channel.discord_id == __channel_id:
                return channel
        return None

    @overload
    def remove(self, _id: int):
        ...

    @overload
    def remove(self, channel: discord.TextChannel):
        ...

    def remove(self, x):
        __channel_id: int = x
        if isinstance(x, discord.TextChannel):
            __channel_id = x.id
        for internChannel in self.__channels:
            if internChannel.discord_id == __channel_id:
                self.__channels.remove(internChannel)
                return


class _AutoThreadingView(discord.ui.View):

    def __init__(self, persistent: bool = True, *, timeout: float = 180.0):
        super().__init__(timeout=None if persistent else timeout)

    @discord.ui.button(label="Javab Dade Shode", custom_id="AutoThreading::Answered", style=discord.ButtonStyle.green)
    async def ButtonAnswered(self, interaction: discord.Interaction, button: discord.ui.Button):
        starter_message = interaction.channel.starter_message
        if starter_message is None:
            starter_message = await interaction.channel.parent.fetch_message(interaction.channel.id)
        if interaction.user.id != starter_message.author.id or not interaction.user.guild_permissions.manage_threads:
            return await interaction.response.send_message("⚠ You are not the owner of this thread!")
        await interaction.response.edit_message(content=f"✅ This Thread has been marked answered by "
                                                        f"{interaction.user.mention}", view=None)
        await interaction.message.channel.edit(
            name=f"{AutoThreading.EMOJIS['ANSWERED']} {interaction.message.channel.name[2:]} [ANSWERED]",
            archived=True, locked=True, reason=f"Answer Command by {interaction.user.name}#"
                                               f"{interaction.user.discriminator}")

    @discord.ui.button(label="Taghir Name Thread", custom_id="AutoThreading::Rename", style=discord.ButtonStyle.blurple)
    async def ButtonRename(self, interaction: discord.Interaction, button: discord.ui.Button):
        starter_message = interaction.channel.starter_message
        if starter_message is None:
            starter_message = await interaction.channel.parent.fetch_message(interaction.channel.id)
        if interaction.user.id != starter_message.author.id or not interaction.user.guild_permissions.manage_threads:
            return await interaction.response.send_message("⚠ You are not the owner of this thread!")
        renameText = _AutoThreadingInputModal(title="Rename Thread", label="Esm Jadid Thread:",
                                              style=discord.TextStyle.short)
        await interaction.response.send_modal(renameText)
        await renameText.wait()
        await interaction.channel.edit(name=f"{AutoThreading.EMOJIS['OPEN']} {renameText.input.value}")
        self.ButtonRename.disabled = True
        await interaction.message.edit(view=self)


class _AutoThreadingInputModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, style: discord.TextStyle, *, placeholder: str = None,
                 timeout: float = 500,
                 max_length: int = 1000):
        self.input = discord.ui.TextInput(label=label, style=style, placeholder=placeholder, max_length=max_length)
        super().__init__(title=title, timeout=timeout)
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message(content="✅ Submitted!", ephemeral=True)
        except discord.NotFound as e:
            await interaction.followup.send(content="✅ Submitted!", ephemeral=True)
        self.stop()


class AutoThreading(commands.Cog):
    EMOJIS = {
        "ANSWERED": "🟢",  # Green Circle
        "OPEN": "🟡"  # Yellow Circle
    }

    def __init__(self, bot: PDBot):
        self.__bot: PDBot = bot
        self.__dataBase: DatabaseHandler = None
        self.__cache: _AutoThreadingCache = _AutoThreadingCache()
        self.__logger = Logger("PDBot.AutoThreading")

    async def cog_load(self) -> None:
        self.__dataBase = DatabaseHandler(self.__bot.config.DataBase.AutoThreading['SRC'])
        await self.__dataBase.init()
        if self.__bot.config.DataBase.AutoThreading['INIT']:
            await self.__dataBase.cursor.execute("CREATE TABLE Channels ("
                                                 "CHANNEL_ID INT NOT NULL,"
                                                 " CREATION_TEXT TEXT DEFAULT '')")
            await self.__dataBase.connection.commit()
            self.__logger.info("Inited Database and created needed tables!")
            new_data = self.__bot.config.data
            new_data['DataBase']['AutoThreading']['INIT'] = False
            self.__bot.config.update(new_data)
        self.__bot.add_view(_AutoThreadingView())
        await self.__loadChannels()
        self.__logger.info("Extension Loaded!")

    async def cog_unload(self) -> None:
        await self.__dataBase.kill()
        self.__logger.info("Extension Unloaded! Database connection closed")

    async def __loadChannels(self) -> None:
        await self.__dataBase.cursor.execute("SELECT * FROM Channels")
        __db_channels = await self.__dataBase.cursor.fetchall()
        for CHANNEL_ID, CREATION_TEXT in __db_channels:
            channel = self.__bot.get_channel(CHANNEL_ID)
            if channel is None:
                channel = await self.__bot.fetch_channel(CHANNEL_ID)
                if channel is None:
                    self.__logger.warning(
                        f"Failed to Get AutoThreading Channel  (ID={CHANNEL_ID}) Ignoring..")
                    continue
            self.__cache.add(channel, CREATION_TEXT)
            self.__logger.debug(f"Cached AutoThreading Channel (ID={CHANNEL_ID})")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or isinstance(message.channel, discord.DMChannel):
            return
        self.__logger.debug(
            f"on_message (channel={message.channel}, content={message.content},"
            f" author={message.author.name}#{message.author.discriminator}, type={type(message.channel)},"
            f" cached={message.channel in self.__cache}) ")
        if message.channel in self.__cache:
            _thread = await message.create_thread(name=f"{AutoThreading.EMOJIS['OPEN']} {message.author.name}'s Thread",
                                                  reason="AutoThreading",
                                                  auto_archive_duration=4320)
            await _thread.send(
                content=self.__cache.get(message.channel).creation_text.replace("{user}", message.author.mention),
                view=_AutoThreadingView())

    @discord.app_commands.command(name="autothreading",
                                  description="autothreading related commands (Admin Only)")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.describe(action="Action to take",
                                   channel="the channel to take action on. if not given, current channel will be used!")
    @discord.app_commands.guild_only()
    async def ATCommand(self, interaction: discord.Interaction,
                        action: typing.Literal["Enable", "Disable", "Change Creation Text", "Info"],
                        channel: typing.Optional[discord.TextChannel]):
        if channel is None:
            channel = interaction.channel
        if action == "Enable":
            if channel in self.__cache:
                return await ErrorHandler.SendError(interaction,
                                                    f"Channel (#{channel.name}) is already AutoThreaded!!")
            ctModal = _AutoThreadingInputModal(
                title="AutoThreading Creation Text",
                label="Creation Text: ", placeholder="Example : \"this thread is created for you {user}\"",
                style=discord.TextStyle.paragraph)
            try:
                await interaction.response.send_modal(ctModal)
            except discord.NotFound:
                await interaction.followup.send(content="test")
                return self.__logger.warning("ATCommand.Enable took more then 3 seconds to respond!!")
            await ctModal.wait()
            await self.__dataBase.cursor.execute("INSERT INTO Channels VALUES (?, ?)",
                                                 [channel.id, ctModal.input.value])
            await self.__dataBase.connection.commit()
            self.__cache.add(channel, ctModal.input.value)
            await interaction.followup.send(content=f"✅ AutoThreading Enabled on (#{channel.name})", ephemeral=True)

        elif action == "Disable":
            if channel not in self.__cache:
                return await ErrorHandler.SendError(interaction, f"Channel ({channel.name}) is not AutoThreaded!!")

            self.__cache.remove(channel)
            await self.__dataBase.cursor.execute("DELETE FROM Channels WHERE CHANNEL_ID = (?)", (channel.id,))
            await self.__dataBase.connection.commit()
            await interaction.response.send_message(content=f"✅ AutoThreading has been disabled on this channel by the "
                                                            f"command of {interaction.user.mention}!")
        elif action == "Change Creation Text":
            if channel not in self.__cache:
                return await ErrorHandler.SendError(interaction, f"Channel ({channel.name}) is not AutoThreaded!!")
            ctModal = _AutoThreadingInputModal("Creation Text", label="New Creation Text:",
                                               style=discord.TextStyle.paragraph,
                                               placeholder="Example: \"this thread is created for you {user}\"", )
            await interaction.response.send_modal(ctModal)
            await ctModal.wait()
            await self.__dataBase.cursor.execute("UPDATE Channels SET CREATION_TEXT = (?) WHERE CHANNEL_ID = (?) ",
                                                 (ctModal.input.value, channel.id))
            self.__cache.get(channel).creation_text = ctModal.input.value
            await self.__dataBase.connection.commit()
            await interaction.response.send_message(content=f"✅ AutoThreading has been disabled on this channel by the "
                                                            f"command of {interaction.user.mention}!")
        elif action == "Info":
            _msg = "Currently Active Channels are:\n"
            for atChannel in self.__cache:
                _msg += f"{atChannel.channel.mention}\n"
            await interaction.response.send_message(content=_msg, ephemeral=True)


async def setup(bot: PDBot):
    if not bot.config.Features.AUTO_THREADING:
        return bot.logger.info("Extension AUTO_THREADING have been set to false in config, ignoring loading.")
    await bot.add_cog(AutoThreading(bot), guild=bot.superGuild)