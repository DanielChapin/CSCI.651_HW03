#align(center + horizon)[
  #text(size: 24pt)[*CSCI.651 HW3 Report*]

  #text(size: 16pt)[Daniel Chapin]

  #text(size: 12pt)[#datetime.today().display()]
]

#set heading(numbering: "1.")

#outline()
#pagebreak()

= Introduction

For usage instructions, please reference `README.md`.

= Setup

First, setting up the unstable tunnel to simulate network conditions:
```sh
./demo.sh unstable_tunnel
```

Then, in another terminal, start the receiver (using the tunnel):
```sh
./demo.sh file_recepticle --port 4381 --sender-port 4380 ../out/message.txt
```

Finally, in another terminal, start the sender (using the tunnel):
```sh
./demo.sh send_file --port 4383 --dest-port 4382 ../sample_files/message.txt
```

= Outputs

== Sender Side

Sender command line output:
```
Sent packet 1/5 (64 bytes).
Sent packet 2/5 (64 bytes).
Sent packet 3/5 (64 bytes).
Sent packet 4/5 (52 bytes).
Packet 1 timed out!
Packet 2 timed out!
Packet 3 timed out!
Packet 4 timed out!
[WARN] Sender event queue emptied without finishing transfer.
Sent packet 1/5 (64 bytes).
Recieved ACK for seq=1
Sent packet 2/5 (64 bytes).
Sent packet 3/5 (64 bytes).
Sent packet 4/5 (52 bytes).
Sent packet 5/5 (0 bytes).
Packet 2 timed out!
Packet 3 timed out!
Packet 4 timed out!
Packet 5 timed out!
[WARN] Sender event queue emptied without finishing transfer.
Sent packet 2/5 (64 bytes).
Recieved invalid ACK packet!
Sent packet 3/5 (64 bytes).
Sent packet 4/5 (52 bytes).
Recieved ACK for seq=1
Low ACK (ACK=1 < seq=2)
Sent packet 2/5 (64 bytes).
Sent packet 3/5 (64 bytes).
Sent packet 4/5 (52 bytes).
Recieved invalid ACK packet!
Sent packet 5/5 (0 bytes).
Packet 2 timed out!
Packet 3 timed out!
Packet 4 timed out!
Packet 5 timed out!
[WARN] Sender event queue emptied without finishing transfer.
Sent packet 2/5 (64 bytes).
Recieved ACK for seq=2
Recieved ACK for seq=4
Recieved ACK for seq=3
Low ACK (ACK=3 < seq=5)
Sent packet 5/5 (0 bytes).
Packet 5 timed out!
No longer accepting packets.
```

== Receiver Side

Receiver command line output:
```
Recieved packet seq=1, expected seq=1
Delivered packet seq=1 (64 bytes).
Timed out waiting for seq=2
Malformed packet (seq=2)!
Recieved packet seq=1, expected seq=2
Unexpected seq, ACKing seq=1.
Timed out waiting for seq=2
Malformed packet (seq=2)!
Recieved packet seq=3, expected seq=2
Unexpected seq, ACKing seq=1.
Malformed packet (seq=2)!
Recieved packet seq=5, expected seq=2
Unexpected seq, ACKing seq=1.
Recieved packet seq=2, expected seq=2
Delivered packet seq=2 (64 bytes).
Recieved packet seq=3, expected seq=3
Delivered packet seq=3 (64 bytes).
Malformed packet (seq=4)!
Recieved packet seq=4, expected seq=4
Delivered packet seq=4 (52 bytes).
Timed out waiting for seq=5
Recieved packet seq=5, expected seq=5
Delivered packet seq=5 (0 bytes).
Deliverer requested to stop receiving.
Receiver finished receiving.
Wrote file to '../out/message.txt'
```

= Observations

There are a number of insights to be drawn from the outputs of the sender and receiver sides.

== Corrupted Packets

Starting with the most obvious - corrupted packets.
Corrupted packets are detected on both ends using checksums.
When a checksum is invalid, the sides have the following behaviors:

=== Receiver Side

The receiver simply discards the corrupted packets.
Example from the output:
```
Malformed packet (seq=2)!
Recieved packet seq=3, expected seq=2
Unexpected seq, ACKing seq=1.
Malformed packet (seq=2)!
Recieved packet seq=5, expected seq=2
Unexpected seq, ACKing seq=1
```

The reason for simply discarding these packets is because of the pipelined nature of Go-Back-N.
The receiver only cares about packets in order, so any corrupted packets are irrelevant until the missing packets are received correctly.
As such, the receiver can simply wait for another packet to arrive and check if it's the expected one.
If it isn't, then it informs the sender of the last correctly received packet via an ACK.
Otherwise, a timeout on the sender side will trigger a retransmission of the missing packets.

=== Sender Side

On the sender side, corrupted ACK packets are also discarded.
Example from the output:
```
Sent packet 2/5 (64 bytes).
Sent packet 3/5 (64 bytes).
Sent packet 4/5 (52 bytes).
Recieved invalid ACK packet!
Sent packet 5/5 (0 bytes).
Packet 2 timed out!
Packet 3 timed out!
Packet 4 timed out!
Packet 5 timed out!
```
Note how all the packets timed-out after the invalid ACK.
This will trigger a retransmission of all unacknowledged packets starting from the last acknowledged packet.

== Reordered Packets

Reordered packets are much more relevant on the receiver side.
Because Go-Back-N requires in-order delivery, the receiver is very picky about which packets it accepts, especially under unstable network conditionsRecieved packet seq=3, expected seq=2
Unexpected seq, ACKing seq=1.
Malformed packet (seq=2)!
Recieved packet seq=5, expected seq=2
Unexpected seq, ACKing seq=1..
On the other hand, the sender is largely unaffected because cummulative ACKs allow it to simply ignore any ACKs that come in out of order.

=== Receiver Side

Example:
```
Recieved packet seq=1, expected seq=2
Unexpected seq, ACKing seq=1.
...
Recieved packet seq=3, expected seq=2
Unexpected seq, ACKing seq=1.
```

As can be seen in the example, when the receiver gets a packet that is out of order, it simply discards it and re-ACKs the last correctly received packet.

=== Sender Side

Example:
```
Sent packet 1/5 (64 bytes).
Recieved ACK for seq=1
...
Recieved ACK for seq=1
Low ACK (ACK=1 < seq=2)
```

Here, the sender receives an ACK for a packet it has already acknowledged.
It simply ignores this ACK and continues sending packets as normal.

== Dropped Packets

Dropped packets are handled similarly to corrupted packets on both sides, however, they are detected via timeouts rather than checksums.

=== Receiver Side

Example:
```
Recieved packet seq=3, expected seq=2
Unexpected seq, ACKing seq=1.
Malformed packet (seq=2)!
Recieved packet seq=5, expected seq=2
Unexpected seq, ACKing seq=1.
```

Here we can see that the sender never received packets with seq=4.

=== Sender Side

Example:
```
Sent packet 1/5 (64 bytes).
Sent packet 2/5 (64 bytes).
Sent packet 3/5 (64 bytes).
Sent packet 4/5 (52 bytes).
Packet 1 timed out!
Packet 2 timed out!
Packet 3 timed out!
Packet 4 timed out!
[WARN] Sender event queue emptied without finishing transfer.
Sent packet 1/5 (64 bytes).
```

When all packets time out, the sender retransmits all unacknowledged packets starting from the last acknowledged packet.

== Inputs & Outputs

=== Receiver Side

Contents of `out/message.txt`:
```
Hello file recepticle!

This is a message from the sender.
It's not super long, but it's long enough that is has to
be split into several packets, which is great for
demonstration purposes.

I hope you are doing well.

Sincerely,
~ send_file.py
```

=== Sender Side

`sample_files/message.txt` contents:
```
Hello file recepticle!

This is a message from the sender.
It's not super long, but it's long enough that is has to
be split into several packets, which is great for
demonstration purposes.

I hope you are doing well.

Sincerely,
~ send_file.py
```
