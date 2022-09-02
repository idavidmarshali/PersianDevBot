import io
import time
import aiohttp
import discord
from discord.ext import commands

from ..utils.database import DatabaseHandler
from ..utils.logger import Logger
from .error_handler import ErrorHandler
from ..bot import PDBot


class _ReportModal(discord.ui.Modal, title="Report Page"):
    def __init__(self, *, timeout: float = 256.0, message_report: bool = False):
        self.topic = discord.ui.TextInput(
            label="Mozoe:", default="Message Report" if message_report else "",
            max_length=128, row=0)

        self.reportMessage = discord.ui.TextInput(
            label="Tozihat:", style=discord.TextStyle.paragraph, placeholder="Tozihat khodeton ro benevisid inja.",
            max_length=1024, row=1)
        self.timedOut: bool = False

        super().__init__(timeout=timeout)
        self.add_item(self.topic)
        self.add_item(self.reportMessage)

    async def on_timeout(self) -> None:
        self.timedOut = True

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(content="✅ Report Sabt Shod!", ephemeral=True)


class Report(commands.Cog):
    def __init__(self, bot: PDBot):
        self.__bot = bot
        self.__logger = Logger("PDBot.Report")
        self.__webhookUrl: str = bot.config.REPORT_WEBHOOK_URL
        self.__dataBase: DatabaseHandler = None
        self.__reportMenu: discord.app_commands.ContextMenu = None
        self.__lastReportId: int = 0

    async def cog_load(self) -> None:
        self.__dataBase = DatabaseHandler(self.__bot.config.DataBase.Reports['SRC'])
        await self.__dataBase.init()
        if self.__bot.config.DataBase.Reports['INIT']:
            await self.__dataBase.cursor.execute("""
                    CREATE TABLE Reports (
                            USER_ID         INT  NOT NULL,
                            USER_NAME       TEXT NOT NULL,
                            REPORT_TOPIC    TEXT NOT NULL,
                            REPORT_TEXT     TEXT NOT NULL,
                            REPORT_ID       INT  NOT NULL,
                            REPORTED_MESSAGE_ID       INT,
                            REPORTED_MESSAGE_USER_ID  INT,
                            REPORTED_MESSAGE_TEXT    TEXT)""")
            await self.__dataBase.connection.commit()
            self.__logger.info("Inited Database and created needed tables!")

            # !! Database is currently on :memory:, if you change that, you need to uncomment this part
            # new_data = self.__bot.config.data
            # new_data['DataBase']['Reports']['INIT'] = False
            # self.__bot.config.update(new_data)

        else:
            await self.__dataBase.cursor.execute("SELECT REPORT_ID FROM Reports ORDER BY REPORT_ID DESC")
            self.__lastReportId = (await self.__dataBase.cursor.fetchone())[0]

        self.__reportMenu = discord.app_commands.ContextMenu(
            name="Report Message",
            callback=self.reportMessage,
            guild_ids=[self.__bot.superGuild.id]
        )
        self.__bot.tree.add_command(self.__reportMenu)

        self.__logger.info("Extension Loaded!")

    async def cog_unload(self) -> None:
        await self.__dataBase.kill()
        self.__bot.tree.remove_command(self.__reportMenu.name, type=self.__reportMenu.type)
        self.__logger.info("Extension Unloaded! Database connection closed.")

    async def __SendReportToWebhook(self, reporter: discord.User, report_id: int, report_topic: str,
                                    report_message: str, reported_message: discord.Message = None):
        async with aiohttp.ClientSession() as aioSession:
            try:
                webhook = discord.Webhook.from_url(self.__webhookUrl, session=aioSession)
                await webhook.send(
                    content=f"Report From: {reporter.mention}\n"
                            f"Report ID : {report_id}\n"
                            f"Report Topic: `{report_topic}`\n"
                            f"Report Message:```\n{report_message}\n```" +
                            (f"\nReported Author: {reported_message.author.mention}\n"
                             f"Reported Message:```\n{reported_message.content}\n```" if reported_message is not None else "Reported Message: None"))
            except ValueError:
                self.__logger.error("Invalid REPORT_WEBHOOK_URL, Report Message Ignored")


    @discord.app_commands.command(name="report",
                                  description="Send a report to moderators")
    @discord.app_commands.guild_only()
    async def report(self, interaction: discord.Interaction):
        self.__lastReportId += 1
        _rtModal = _ReportModal()
        await interaction.response.send_modal(_rtModal)
        await _rtModal.wait()
        if _rtModal.timedOut:
            return await ErrorHandler.SendError(interaction, "Report Form Timeout", followup=True)

        await self.__SendReportToWebhook(interaction.user, self.__lastReportId, _rtModal.topic.value,
                                         _rtModal.reportMessage.value)
        await self.__dataBase.cursor.execute("INSERT INTO Reports (USER_ID, USER_NAME, REPORT_TOPIC, REPORT_TEXT,"
                                             " REPORT_ID) VALUES (?, ?, ?, ?, ?)",
                                             (interaction.user.id, interaction.user.name, _rtModal.topic.value,
                                              _rtModal.reportMessage.value, self.__lastReportId))
        await self.__dataBase.connection.commit()
        return

    @discord.app_commands.guild_only()
    async def reportMessage(self, interaction: discord.Interaction, message: discord.Message):
        self.__lastReportId += 1
        _rtModal = _ReportModal(message_report=True)
        await interaction.response.send_modal(_rtModal)
        await _rtModal.wait()
        if _rtModal.timedOut:
            return await ErrorHandler.SendError(interaction, "Report Form Timeout", followup=True)

        await self.__SendReportToWebhook(interaction.user, self.__lastReportId, _rtModal.topic.value,
                                         _rtModal.reportMessage.value, message)
        await self.__dataBase.cursor.execute("INSERT INTO Reports (USER_ID, USER_NAME, REPORT_TOPIC, REPORT_TEXT,"
                                             " REPORT_ID, REPORTED_MESSAGE_ID, REPORTED_MESSAGE_USER_ID,"
                                             " REPORTED_MESSAGE_TEXT) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                             (interaction.user.id, interaction.user.name, _rtModal.topic.value,
                                              _rtModal.reportMessage.value, self.__lastReportId, message.id,
                                              message.author.id, message.content))
        await self.__dataBase.connection.commit()
        return

    @commands.command()
    @commands.is_owner()
    async def get_reports_csv(self, ctx: commands.Context):
        await self.__dataBase.cursor.execute(
            "SELECT REPORT_ID,USER_ID,USER_NAME,REPORT_TOPIC,REPORT_TEXT,REPORTED_MESSAGE_ID,"
            "REPORTED_MESSAGE_USER_ID,REPORTED_MESSAGE_TEXT FROM Reports")
        all_reports = await self.__dataBase.cursor.fetchall()
        # Opening a memory stream to write csv data and send it
        with io.BytesIO() as memoryOut:
            memoryOut.write(b"REPORT_ID,USER_ID,USER_NAME,REPORT_TOPIC,REPORT_TEXT,REPORTED_MESSAGE_ID,"
                            b"REPORTED_MESSAGE_USER_ID,REPORTED_MESSAGE_TEXT\n")
            for row in all_reports:
                memoryOut.write(repr(row).encode("utf-8").replace(b"(", b"").replace(b")", b"") + b"\n")
            memoryOut.seek(0)
            filename = "reports " + time.strftime("%m-%d-%Y", time.localtime())
            file = discord.File(memoryOut, filename=filename)
            await ctx.author.send(content="all reports until today", file=file)


async def setup(bot: PDBot):
    if not bot.config.Features.REPORTS:
        return bot.logger.info("Extension REPORTS have been set to false in config, ignoring loading.")
    await bot.add_cog(Report(bot), guild=bot.superGuild)
