from UDPDuplex import UDPDuplex
from rdt import GoBackNSender, UDPDuplexGoBackNClient
from argparse import ArgumentParser
from pathlib import Path


def argp():
    p = ArgumentParser()
    p.add_argument("--interface", type=str, default="localhost")
    p.add_argument("--port", type=int, default=4381)
    p.add_argument("--dest", type=str, default="localhost")
    p.add_argument("--dest-port", type=int, default=4382)
    p.add_argument("--window-size", type=int, default=3)
    p.add_argument("localpath", type=Path)
    return p


def main():
    args = argp().parse_args()

    udpd = UDPDuplex(args.interface, args.port, args.dest, args.dest_port)
    gbnc = UDPDuplexGoBackNClient(udpd, 10)

    with open(args.localpath, "br") as in_file:
        gbns = GoBackNSender(gbnc, args.window_size)
        gbns.push(in_file.read())
        # Indicator for end of file
        gbns.push(bytes())
        # Transmit until done
        gbns.start()


if __name__ == "__main__":
    main()
