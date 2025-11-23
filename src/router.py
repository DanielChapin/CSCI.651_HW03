from typing import Any, Callable
from sched import scheduler
from time import time, sleep
from random import random, randrange


class Router:
    """A simulated unreliable router that can drop, corrupt, and delay packets."""
    drop_chance: float
    corrupt_chance: float
    min_delay: float
    max_delay: float
    auto_start: bool

    rxs: dict[int, list[Callable[[bytes], None]]]
    sch: scheduler

    def __init__(self) -> None:
        self.rxs = dict()
        self.sch = scheduler(time, sleep)
        self.auto_start = False

    def register_rx(self, port: int, rx: Callable[[bytes], Any]):
        """
        Registers a receiver callback for a given port.
        @param port  The port number to register the receiver on.
        @param rx    The receiver callback function that takes a bytes object.
        """
        if port not in self.rxs:
            self.rxs[port] = list()
        self.rxs[port].append(rx)

    def unregister_rx(self, port: int, rx: Callable[[bytes], Any]):
        """
        Unregisters a receiver callback from a given port.
        @param port  The port number to unregister the receiver from.
        @param rx    The receiver callback function to remove.
        """
        if port in self.rxs:
            self.rxs[port].remove(rx)
            if not self.rxs[port]:
                del self.rxs[port]

    def output_packet(self, port: int, packet: bytes):
        """
        Outputs a packet to all registered receivers on the given port.
        @param port    The port number to send the packet to.
        @param packet  The packet data to send.
        """
        for rx_handler in self.rxs.get(port, list()):
            rx_handler(packet)

    def corrupt_packet(self, packet: bytes) -> bytes:
        """
        Corrupts a packet by flipping random bits based on the corrupt_chance.
        @param packet  The original packet bytes.
        @return  The corrupted packet bytes.
        """
        bit_len = len(packet) * 8

        result = bytearray(packet)
        cnt = 0
        while random() < self.corrupt_chance and cnt < bit_len:
            bit = randrange(0, bit_len)
            byte_idx = bit // 8
            bit_idx = bit % 8
            result[byte_idx] ^= 1 << bit_idx
            cnt += 1

        return bytes(result)

    def tx(self, port: int, packet: bytes):
        """
        Transmits a packet on a given port, potentially dropping, corrupting, and delaying it.
        @param port    The port number to send the packet to.
        @param packet  The packet data to send.
        """
        if random() < self.drop_chance:
            return

        packet = self.corrupt_packet(packet)

        delay = self.min_delay + random() * (self.max_delay - self.min_delay)
        self.sch.enter(delay, 0, lambda: self.output_packet(port, packet), ())

        if self.auto_start:
            self.start(False)

    def start(self, blocking: bool = True):
        """
        Starts the router's scheduler to process events.
        @param blocking  If True, blocks until all scheduled events are processed.
        """
        self.sch.run(blocking=blocking)
