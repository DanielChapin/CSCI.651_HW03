from UDPDuplex import UDPDuplex
from sys import argv
from time import sleep

port = int(argv[1])
dst_port = int(argv[2])

duplex = UDPDuplex("localhost", port, "localhost", dst_port)


with duplex.create_handle() as handle:
    handle.recv = lambda payload: print(f"From peer: {payload.decode()}")
    counter = 0
    while True:
        handle.send(f"Hello, Peer! (#{counter})".encode())
        counter += 1
        sleep(1)
