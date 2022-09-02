from .bot import PDBot
from .utils.config import ConfigLoader
from .utils.keep_alive import SocketKeepAlive as KeepAlive
import discord
from discord.ext import commands

def BotRunner(cfgPath):
    config = ConfigLoader(cfgPath)
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    bot = PDBot(commands.when_mentioned, intents, config, config.Extensions)
    bot.help_command = None
    bot.run(config.DISCORD_API_SECRET)

def KaRunner(cfgPath):
    config = ConfigLoader(cfgPath)
    kaServer = KeepAlive(config.KeepAlive.HOST, config.KeepAlive.PORT)
    kaServer.run()