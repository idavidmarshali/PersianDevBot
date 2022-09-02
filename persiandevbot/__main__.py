import multiprocessing
import os.path

import discord
from discord.ext import commands

from .bot import PDBot
from .runner import BotRunner, KaRunner
from .utils import SocketKeepAlive as KeepAlive
from .utils import ConfigLoader

from os import environ

environ['DISCORD_API_SECRET'] = "ODEwNTk0Nzc0MTUxMjAwNzk4.GDsSsn.RNd4mLYdNy9O_m-q9Hiv4SXyVZgoD9P3IQatdM"
environ['REPORT_WEBHOOK_URL'] = "https://discord.com/api/webhooks/1014228029725225020/FjTJF9vvH96u-RcU4gCqOGGriBwMLE4aHU3xgS57l9kE-c_AOd_vTwaFFsU7zQDLlEuw"





if __name__ == "__main__":
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    botProcess = multiprocessing.Process(target=BotRunner, args=(config_path,))
    kaProcess = multiprocessing.Process(target=KaRunner, args=(config_path,))
    botProcess.start()
    kaProcess.start()
    botProcess.join()
