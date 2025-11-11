from typing import Callable
from UDPDuplex import UDPDuplex
from router import Router
from threading import Thread


class UnstableTunnel:
    router: Router

    def __init__(self, inner_router: Router) -> None:
        self.router = inner_router

    def start(self, a_interface: UDPDuplex, b_interface: UDPDuplex, host: str = "127.0.0.1"):
        raise NotImplementedError()


class UnstableClient:
    host: str
    port: int
    rcv: Callable[[bytes], None]

    def __init__(self, rcv: Callable[[bytes], None], port: int, host: str = "127.0.0.1"):
        self.host = host
        self.port = port
        self.rcv = rcv

    def start(self):
        raise NotImplementedError()

    def send(self, packet: bytes):
        raise NotImplementedError()
