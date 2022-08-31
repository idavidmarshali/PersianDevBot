import multiprocessing
import os
import discord
from discord.ext import commands
from bot import PDBot
from utils.keep_alive import SocketKeepAlive as KeepAlive
from utils.config import ConfigLoader


def BotRunner():
    config = ConfigLoader("config.json")
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    bot = PDBot(commands.when_mentioned, intents, config, config.Extensions)
    bot.help_command = None
    bot.run(config.DISCORD_API_SECRET)


def KaRunner():
    config = ConfigLoader("config.json")
    kaServer = KeepAlive(config.KeepAlive.HOST, config.KeepAlive.PORT)
    kaServer.run()


if __name__ == "__main__":
    botProcess = multiprocessing.Process(target=BotRunner)
    kaProcess = multiprocessing.Process(target=KaRunner)
    botProcess.start()
    kaProcess.start()
    botProcess.join()



