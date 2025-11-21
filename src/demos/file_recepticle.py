from UDPDuplex import UDPDuplex
from rdt import GoBackNReceiver, UDPDuplexGoBackNClient
from argparse import ArgumentParser
from pathlib import Path


def argp():
    p = ArgumentParser()
    p.add_argument("--interface", type=str, default="localhost")
    p.add_argument("--port", type=int, default=4382)
    p.add_argument("--sender", type=str, default="localhost")
    p.add_argument("--sender-port", type=int, default=4381)
    p.add_argument("localpath", type=Path)
    return p


def main():
    args = argp().parse_args()

    udpd = UDPDuplex(args.interface, args.port, args.sender, args.sender_port)
    gbnc = UDPDuplexGoBackNClient(udpd, 10)

    with open(args.localpath, "bw") as out_file:
        def write_block(block: bytes) -> bool:
            if len(block) == 0:
                # Indicating end-of-file
                return False

            out_file.write(block)
            return True
        gbnr = GoBackNReceiver(gbnc)
        gbnr.recv(write_block)

    print(f"Wrote file to '{args.localpath}'")


if __name__ == "__main__":
    main()
