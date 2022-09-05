from flask import Flask, Response
import socket
from socket import socket as Socket
from utils.logger import Logger


class SocketKeepAlive:
    """
    a KeepAlive Class which starts a socket server on the given host/port for keeping the repo alive in `replit`.

    **any connection requests received by the socket is ignored and closed**
    """
    def __init__(self, host: str, port: int):
        self.__socket = Socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__address = (host, port)
        self.__logger = Logger("PDBot.SocketKeepAlive")
        self.__socket.bind((host, port))

    def run(self):
        self.__socket.listen()
        self.__logger.info(f"Listening to bound address {self.__address}")
        while True:
            soc, addr = self.__socket.accept()
            self.__logger.info(f"Connection request accepted from {addr=}")
            soc.close()


class FlaskKeepAlive:
    # Reserve class for use instead of `SocketKeepAlive`
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
