from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Callable, Tuple
from socket import socket, AF_INET, SOCK_DGRAM as SOCK_UDP, timeout
from cfg import BUF_SIZE
from threading import Event, Thread
from contextlib import AbstractContextManager


@dataclass
class JoinedUDPHandle(AbstractContextManager):
    """A handle for sending and receiving UDP packets."""
    sock: socket
    dst: Tuple[str, int]
    recv: Callable[[bytes], Any] | None = None
    close_event: Event = field(default_factory=Event)
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
        """
        Listens for incoming UDP packets and calls the recv callback when data is received.
        This method should run in a separate thread and continues until the handle is closed.
        """
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

    def listen_once(self) -> bytes:
        """
        Listens for a single incoming UDP packet and returns the data.
        This method blocks until a packet is received or a timeout occurs.
        """
        return self.sock.recv(BUF_SIZE)

    def send(self, payload: bytes):
        """
        Sends a UDP packet to the destination.
        @param payload  The data to send.
        """
        self.sock.sendto(payload, self.dst)

    def close(self):
        """
        Closes the UDP handle, stopping any listening threads and closing the socket.
        """
        self.sock.close()
        self.close_event.set()


@dataclass
class UDPDuplex:
    """A UDP interface that can send and receive packets to/from a specified destination."""
    host: str
    port: int
    dst: str
    dst_port: int

    def create_handle(self, recv: Callable[[bytes], Any] | None = None) -> JoinedUDPHandle:
        """
        Creates a JoinedUDPHandle for sending and receiving packets.
        @param recv  An optional callback function to handle received packets.
        @return  A JoinedUDPHandle instance.
        """
        handle = JoinedUDPHandle(socket(
            AF_INET, SOCK_UDP), (self.dst, self.dst_port), recv)

        handle.sock.settimeout(1.0)
        handle.sock.bind((self.host, self.port))

        return handle
