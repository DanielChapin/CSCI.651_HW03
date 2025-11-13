from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Callable, Tuple
from socket import socket, AF_INET, SOCK_DGRAM as SOCK_UDP, timeout
from cfg import BUF_SIZE
from threading import Event, Thread
from contextlib import AbstractContextManager


@dataclass
class JoinedUDPHandle(AbstractContextManager):
    sock: socket
    dst: Tuple[str, int]
    recv: Callable[[bytes], Any] | None = None
    close_event: Event = field(default=Event())
    listen_thread: Thread | None = field(default=None)

    def __enter__(self) -> "JoinedUDPHandle":
        self.listen_thread = Thread(target=lambda: self.listen())
        self.listen_thread.start()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> bool | None:
        self.close()
        if self.listen_thread:
            self.listen_thread.join()
        return False

    def listen(self):
        while not self.close_event.is_set():
            try:
                data = self.listen_once()
                if self.recv:
                    self.recv(data)
            except timeout:
                continue
            except OSError:
                # Socket is no longer valid
                break

    def listen_once(self):
        return self.sock.recv(BUF_SIZE)

    def send(self, payload: bytes):
        self.sock.sendto(payload, self.dst)

    def close(self):
        self.sock.close()
        self.close_event.set()


@dataclass
class UDPDuplex:
    host: str
    port: int
    dst: str
    dst_port: int

    def create_handle(self, recv: Callable[[bytes], Any] | None = None) -> JoinedUDPHandle:
        handle = JoinedUDPHandle(socket(
            AF_INET, SOCK_UDP), (self.dst, self.dst_port), recv)

        handle.sock.settimeout(1.0)
        handle.sock.bind((self.host, self.port))

        return handle
