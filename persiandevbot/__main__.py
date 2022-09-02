import multiprocessing
import os.path

import discord
from discord.ext import commands

from .bot import PDBot
from .runner import BotRunner, KaRunner
from .utils import SocketKeepAlive as KeepAlive
from .utils import ConfigLoader

if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    botProcess = multiprocessing.Process(target=BotRunner, args=(config_path,))
    kaProcess = multiprocessing.Process(target=KaRunner, args=(config_path,))
    botProcess.start()
    kaProcess.start()
    botProcess.join()
