from UDPDuplex import UDPDuplex
from router import Router
from time import sleep


class UnstableTunnel:
    """A tunnel that uses an unreliable router to transmit packets between two UDP interfaces."""
    router: Router

    def __init__(self, inner_router: Router) -> None:
        """
        Initializes the UnstableTunnel with an inner Router instance.
        @param inner_router  The Router instance to use for simulating an unreliable network.
        """
        self.router = inner_router

    def start(self, a_interface: UDPDuplex, b_interface: UDPDuplex):
        """
        Starts the tunnel between two UDP interfaces.
        Note that this function blocks indefinitely.
        @param a_interface  The first UDPDuplex interface.
        @param b_interface  The second UDPDuplex interface.
        """
        self.router.auto_start = True
        with a_interface.create_handle() as a_handle, b_interface.create_handle() as b_handle:
            self.router.register_rx(2, lambda packet: b_handle.send(packet))
            self.router.register_rx(1, lambda packet: a_handle.send(packet))

            a_handle.recv = lambda packet: self.router.tx(2, packet)
            b_handle.recv = lambda packet: self.router.tx(1, packet)

            # TODO This is really stupid but it does in fact work
            while True:
                sleep(1000)
