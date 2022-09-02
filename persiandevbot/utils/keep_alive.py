import socket
from flask import Flask, Response
from socket import socket as Socket

from .logger import Logger



class SocketKeepAlive:
    def __init__(self, host: str, port: int, *args, **kwargs):
        self.__socket = Socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__logger = Logger("PDBot.SocketKeepAlive")
        self.__socket.bind((host, port))

    def run(self):
        self.__socket.listen()
        self.__logger.info(f"Listening to binded address")
        while True:
            soc, addr = self.__socket.accept()
            self.__logger.info(f"Connection request accepted from {addr=}")
            soc.close()


class FlaskKeepAlive:
    def __init__(self, host: str, port: int, name: str = "PD_KEEP_ALIVE"):
        self.__app = Flask(name)
        self.__host = host
        self.__port = port
        self.__app.add_url_rule("/", None, self.__index)

    @staticmethod
    def __index():
        return Response(status=200)

    def run(self):
        self.__app.run(self.__host, self.__port, threaded=True)
