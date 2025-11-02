from router import Router

router = Router()
router.drop_chance = 0.1
router.corrupt_chance = 0.01
router.min_delay = 0.1
router.max_delay = 4

router.register_rx(1, lambda pkt: print(pkt.hex()))

for i in range(10):
    packet = int.to_bytes(i)
    print(f"Sending: {packet.hex()}")
    router.tx(1, packet)

router.start()
