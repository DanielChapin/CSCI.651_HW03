# CSCI.651 Homework 03 - RDT

Author: Daniel Chapin (dsc4984)

## Usage Instructions

This project has a series of demos for individual parts as well as the file transfer programs.

## Demos

To run a demo, either run `demo.sh <demo_name>` or...
```sh
source venv/bin/activate
cd src
python3 -m demos.<demo_name>
```

### udp_duplex

A simple UDP duplex demonstration that sends data back and forth.
This demo takes two command line parameters - the host port and the destination port.

For instance, in one shell:
```sh
./demo.sh udp_duplex 4381 4382
```
and in another:
```sh
./demo.sh udp_duplex 4382 4381
```

### tunnel

This program demonstrates the unstable tunnel (which implements randomized packet drops, corruption, delays, and reordering).
This program takes no command line arguments.
It is instead configured through the `TUNNEL_*` values in `src/cfg.py`.
The parameters of the unstable router can be seen and modified in `src/demos/tunnel.py`.

To use this demo, we need to set up the tunnel and open a duplex connection into both ends.

This demo assumes that the cfg has the following values:

```py
TUNNEL_A_IN = 4380
TUNNEL_A_DST = 4381
TUNNEL_B_IN = 4382
TUNNEL_B_DST = 4383
```

First shell:
```sh
./demo.sh tunnel
```
Second shell:
```sh
./demo udp_duplex 4381 4380
```
Third shell:
```sh
./demo udp_duplex 4383 4382
```