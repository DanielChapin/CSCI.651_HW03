from UDPDuplex import UDPDuplex
from rdt import GoBackNSender, UDPDuplexGoBackNClient
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path


def argp():
    p = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument("--interface", type=str, default="localhost",
                   help="Interface to bind to")
    p.add_argument("--port", type=int, default=4381,
                   help="Port to bind to")
    p.add_argument("--dest", type=str, default="localhost",
                   help="Destination interface")
    p.add_argument("--dest-port", type=int, default=4382,
                   help="Destination port")
    p.add_argument("--window-size", type=int, default=3,
                   help="Go-Back-N window size")
    p.add_argument("localpath", type=Path,
                   help="Local path of the file to send")
    return p


def main():
    args = argp().parse_args()

    udpd = UDPDuplex(args.interface, args.port, args.dest, args.dest_port)
    gbnc = UDPDuplexGoBackNClient(udpd, 10)

    with open(args.localpath, "br") as in_file:
        gbns = GoBackNSender(gbnc, args.window_size)
        gbns.push(in_file.read())
        # Indicator for end of file
        gbns.push(bytes(0))
        # Transmit until done
        gbns.start()


if __name__ == "__main__":
    main()
