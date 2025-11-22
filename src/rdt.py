from typing import Callable
import zlib
from UDPDuplex import UDPDuplex, JoinedUDPHandle
import sched
import time
from asyncio import Event
from threading import Thread


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
        self.handle.sock.settimeout(timeout)

    def send(self, payload: bytes):
        self.handle.send(payload)

    def recv(self) -> bytes | None:
        try:
            return self.handle.listen_once()
        except TimeoutError:
            return None


class GoBackNSender:
    client: GoBackNClient
    n: int
    curr_seq: int
    seq_max: int
    buf: list[bytes]

    def __init__(self, client: GoBackNClient, n: int) -> None:
        assert n > 0
        self.client = client
        self.n = n
        self.curr_seq = 1
        self.seq_max = self.curr_seq + self.n
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
        max_len = 64
        if len(data) < max_len:
            self.buf.append(data)
        else:
            payloads = [data[i:i+max_len]
                        for i in range(0, len(data), max_len)]
            self.buf += payloads

    def start(self):
        """Blocking function that transmits until all queued data has been received by the client"""
        sch = sched.scheduler(time.time, time.sleep)
        self.seq_max = min(self.seq_max, len(self.buf))

        def timeout_ev(seq_n: int):
            if seq_n < self.curr_seq:
                # Old timeout that's no longer relevant
                return
            print(f"Packet {seq_n} timed out!")

        def send_ev(seq_n: int, payload: bytes):
            if seq_n < self.curr_seq:
                # Old send that's no longer relevant
                return
            pkt = self.create_packet(payload, seq_n)
            self.client.send(pkt)
            sch_timeout(seq_n)
            print(
                f"Sent packet {seq_n}/{len(self.buf)} ({len(payload)} bytes).")

            # Checking if another send should be scheduled and scheduling it if need be
            if seq_n < self.seq_max:
                sch_send(seq_n + 1, self.buf[seq_n])

        def recv_ev(pkt: bytes):
            res = self.decode_ack_packet(pkt)
            if res is None:
                print(f"Recieved invalid ACK packet!")
                return

            ack_seq: int = res
            print(f"Recieved ACK for seq={ack_seq}")
            if ack_seq < self.curr_seq:
                # If the ACK is low, then the sender rejected a packet,
                # and we resend the start of the current window.
                print(f"Low ACK (ACK={ack_seq} < seq={self.curr_seq})")
                ev = sch_send(self.curr_seq, self.buf[self.curr_seq - 1])
                for ex_ev in sch.queue:
                    if ex_ev != ev:
                        sch.cancel(ex_ev)
            elif ack_seq > self.seq_max:
                print(f"Recieved ACK above expected range... ignoring.")
            else:
                # Cumulative seqs
                delta_seq = ack_seq - self.curr_seq + 1
                self.curr_seq += delta_seq
                self.seq_max = min(self.seq_max + delta_seq, len(self.buf))

        def sch_timeout(seq_n: int, delay: float = 10) -> sched.Event:
            return sch.enter(delay, 0, timeout_ev, (seq_n,))

        def sch_send(seq_n: int, payload: bytes, delay: float | None = None) -> sched.Event:
            if delay is None:
                # Max of 500 bits per second on link
                delay = (len(payload) + 12) * 8 / 500
            return sch.enter(delay, 0, send_ev, (seq_n, payload))

        def recver(end_ev: Event):
            while not end_ev.is_set():
                pkt_in = self.client.recv()
                if pkt_in is None:
                    continue
                recv_ev(pkt_in)
            print("No longer accepting packets.")

        recver_end_ev = Event()
        recver_thread = Thread(target=recver, args=(recver_end_ev,))

        if len(self.buf) > 0:
            sch_send(self.curr_seq, self.buf[0])

        recver_thread.start()
        while True:
            sch.run(blocking=True)
            if self.curr_seq < len(self.buf):
                print("[WARN] Sender event queue emptied without finishing transfer.")
                sch_send(self.curr_seq, self.buf[self.curr_seq - 1])
                time.sleep(1)
            else:
                break
        recver_end_ev.set()
        recver_thread.join()


class GoBackNReceiver:
    client: GoBackNClient
    curr_seq: int

    def __init__(self, client: GoBackNClient) -> None:
        self.client = client
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
                print(f"Timed out waiting for seq={self.curr_seq}")
                continue

            res = self.decode_packet(pkt)
            if res == None:
                print(f"Malformed packet (seq={self.curr_seq})!")
                continue

            seq, data = res
            print(f"Recieved packet seq={seq}, expected seq={self.curr_seq}")

            if seq == self.curr_seq:
                should_continue = deliver(data)
                print(f"Delivered packet seq={seq} ({len(data)} bytes).")
                self.client.send(self.create_ack_packet())
                self.curr_seq += 1
                if not should_continue:
                    print("Deliverer requested to stop receiving.")
                    break
            else:
                print(f"Unexpected seq, ACKing seq={self.curr_seq - 1}.")
                self.client.send(self.create_ack_packet(self.curr_seq - 1))
        print("Receiver finished receiving.")
