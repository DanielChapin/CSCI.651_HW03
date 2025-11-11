from dataclasses import dataclass


@dataclass
class UDPDuplex:
    in_port: int
    out_port: int
    dst: str
    dst_port: int
