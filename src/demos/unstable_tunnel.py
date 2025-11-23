from tunnel import UnstableTunnel
from router import Router
from cfg import TUNNEL_A_IN, TUNNEL_A_DST, TUNNEL_B_IN, TUNNEL_B_DST
from UDPDuplex import UDPDuplex

a = UDPDuplex("localhost", TUNNEL_A_IN, "localhost", TUNNEL_A_DST)
b = UDPDuplex("localhost", TUNNEL_B_IN, "localhost", TUNNEL_B_DST)

router = Router()
router.drop_chance = 0.15
router.corrupt_chance = 0.25
router.min_delay = 1
router.max_delay = 4

tunnel = UnstableTunnel(router)
tunnel.start(a, b)
