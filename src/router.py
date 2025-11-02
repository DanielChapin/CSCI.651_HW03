from typing import Callable
from sched import scheduler
from time import time, sleep
from random import random, sample, randrange


class Router:
    drop_chance: float
    corrupt_chance: float
    min_delay: float
    max_delay: float

    rxs: dict[int, list[Callable[[bytes], None]]]
    sch: scheduler

    def __init__(self) -> None:
        self.rxs = dict()
        self.sch = scheduler(time, sleep)

    def register_rx(self, port: int, rx: Callable[[bytes], None]):
        if port not in self.rxs:
            self.rxs[port] = list()
        self.rxs[port].append(rx)

    def output_packet(self, port: int, packet: bytes):
        for rx_handler in self.rxs.get(port, list()):
            rx_handler(packet)

    def corrupt_packet(self, packet: bytes) -> bytes:
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
        if random() < self.drop_chance:
            return

        if random() < self.corrupt_chance:
            packet = self.corrupt_packet(packet)

        delay = self.min_delay + random() * (self.max_delay - self.min_delay)
        self.sch.enter(delay, 0, lambda: self.output_packet(port, packet), ())

    def start(self, blocking: bool = True):
        self.sch.run(blocking=blocking)
