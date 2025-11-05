from router import Router
from queue import Queue
import zlib


class GoBackNClient:
    router: Router
    in_port: int
    out_port: int

    def __init__(self, router: Router, in_port: int, out_port: int) -> None:
        self.router = router
        self.in_port = in_port
        self.out_port = out_port
        self.router.register_rx(self.in_port, self.rx_handler)

    def rx_handler(self, packet: bytes):
        raise NotImplementedError("rx_handler must be implemented by subclass")

    def tx(self, packet: bytes):
        self.router.tx(self.out_port, packet)


class GoBackNSender(GoBackNClient):
    n: int
    curr_seq: int
    buf: Queue[bytes]
    timeout: float

    def __init__(self, n: int) -> None:
        assert n > 0
        self.n = n
        self.curr_seq = 0
        self.buf = Queue(maxsize=n)
        self.timeout = 7.5

    def create_packet(self, data: bytes) -> bytes:
        # Packet format: <checksum(4 bytes)><seq_num(4 bytes)><data_size(4 bytes)><data(data_size bytes)>
        assert self.curr_seq < 2**32
        seq_bytes = self.curr_seq.to_bytes(4, byteorder="big")

        assert len(data) < 2**32
        data_size = len(data).to_bytes(4, byteorder="big")

        dat = seq_bytes + data_size + data
        checksum = zlib.crc32(dat).to_bytes(4, byteorder="big")

        return checksum + dat


class GoBackNReceiver(GoBackNClient):
    curr_seq: int

    def __init__(self) -> None:
        self.curr_seq = 0

    def create_ack_packet(self, seq_num: int) -> bytes:
        # ACK Packet format: <checksum(4 bytes)><seq_num(4 bytes)>
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
