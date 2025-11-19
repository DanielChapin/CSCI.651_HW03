from typing import Any, Callable
import zlib
from UDPDuplex import UDPDuplex, JoinedUDPHandle


class GoBackNClient:
    timeout: float | None

    def __init__(self, timeout: float | None) -> None:
        self.timeout = timeout

    def send(self, payload: bytes):
        raise NotImplementedError()

    def recv(self) -> bytes | None:
        raise NotImplementedError()


class UDPDuplexGoBackNClient(GoBackNClient):
    duplex: UDPDuplex
    handle: JoinedUDPHandle

    def __init__(self, duplex: UDPDuplex, timeout: float | None) -> None:
        super().__init__(timeout)
        self.duplex = duplex
        self.handle = duplex.create_handle()

    def send(self, payload: bytes):
        self.handle.send(payload)

    def recv(self) -> bytes | None:
        return self.handle.listen_once()


class GoBackNSender:
    client: GoBackNClient
    n: int
    curr_seq: int
    buf: list[bytes]

    def __init__(self, client: GoBackNClient, n: int) -> None:
        assert n > 0
        self.client = client
        self.n = n
        self.curr_seq = 1
        self.buf = list()

    def create_packet(self, data: bytes, seq_num: int | None = None) -> bytes:
        # Packet format: <checksum(4 bytes)><seq_num(4 bytes)><data_size(4 bytes)><data(data_size bytes)>
        if seq_num is None:
            seq_num = self.curr_seq

        assert seq_num < 2**32
        seq_bytes = seq_num.to_bytes(4, byteorder="big")

        assert len(data) < 2**32
        data_size = len(data).to_bytes(4, byteorder="big")

        dat = seq_bytes + data_size + data
        checksum = zlib.crc32(dat).to_bytes(4, byteorder="big")

        return checksum + dat

    def termination_packet(self, seq_num: int | None = None):
        return self.create_packet(bytes(), seq_num=seq_num)

    def decode_ack_packet(self, packet: bytes) -> int | None:
        if len(packet) != 8:
            return None

        recv_checksum = int.from_bytes(packet[0:4], byteorder="big")
        seq_num = int.from_bytes(packet[4:8], byteorder="big")

        computed_checksum = zlib.crc32(packet[4:8])
        if recv_checksum != computed_checksum:
            return None

        return seq_num

    def push(self, data: bytes):
        payloads = [data[i:i+64] for i in range(0, len(data), 64)]
        self.buf += payloads

    def start(self):
        """Blocking function that transmits until all queued data has been received by the client"""
        raise NotImplementedError()
        while len(self.buf) > 0:
            pass


class GoBackNReceiver:
    client: GoBackNClient
    curr_seq: int
    deliver: Callable[[bytes], None]

    def __init__(self, client: GoBackNClient, deliver: Callable[[bytes], None]) -> None:
        self.client = client
        self.deliver = deliver
        self.curr_seq = 1

    def create_ack_packet(self, seq_num: int | None = None) -> bytes:
        # ACK Packet format: <checksum(4 bytes)><seq_num(4 bytes)>
        if seq_num is None:
            seq_num = self.curr_seq
        seq_bytes = seq_num.to_bytes(4, byteorder="big")
        checksum = zlib.crc32(seq_bytes).to_bytes(4, byteorder="big")
        return checksum + seq_bytes

    def decode_packet(self, packet: bytes) -> tuple[int, bytes] | None:
        """Returns (seq_num, data) if packet is valid, else None."""
        if len(packet) < 12:
            return None

        recv_checksum = int.from_bytes(packet[0:4], byteorder="big")
        seq_num = int.from_bytes(packet[4:8], byteorder="big")
        data_size = int.from_bytes(packet[8:12], byteorder="big")
        if len(packet) != 12 + data_size:
            return None

        data = packet[12:12+data_size]
        computed_checksum = zlib.crc32(packet[4:12+data_size])
        if recv_checksum != computed_checksum:
            return None

        return seq_num, data

    def recv(self, deliver: Callable[[bytes], bool]):
        while True:
            pkt = self.client.recv()
            if pkt == None:
                print("[GBNR] Timed out")
                continue

            res = self.decode_packet(pkt)
            if res == None:
                print("[GBNR] Couldn't parse packet!")
                continue

            seq, data = res

            if seq == self.curr_seq:
                # Empty packet will be considered connection terminator
                if len(data) == 0:
                    break
                deliver(data)
                self.client.send(self.create_ack_packet())
                self.curr_seq += 1
            else:
                self.client.send(self.create_ack_packet(self.curr_seq - 1))
