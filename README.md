# CSCI.651 Homework 03 - RDT

Author: Daniel Chapin (dsc4984)

This project is structured into abstract implementation and demos.
All of the implementation code can be found in `src/*.py`, and all of the demos can be found in `src/demos`.
Note that the file sharing is also implemented via the demos so that the unstable router demo (`tunnel`) can be used with file sharing to induce unstable network conditions.

The style of file sharing I went with was a server (`file_recepticle`) that waits for a connect and recieves a file from a sender.
As such, the sender initiates the connection and selects the file.

## Usage Instructions

This project has a series of demos for individual parts as well as the file transfer programs, which are also implemented in the same way as the demos (explained below).
Each demo has its own command line arguments that are explained in their own sections.

This project uses no dependencies, but a `requirements.txt` is provided nonetheless.

## Demos

To run a demo, either run `demo.sh <demo_name> ...args...` or...
```sh
source venv/bin/activate
cd src
python3 -m demos.<demo_name>
```

Please note that if using `demo.sh`, all paths must either be global or relative to `src/`.

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
./demo.sh udp_duplex 4381 4380
```
Third shell:
```sh
./demo.sh udp_duplex 4383 4382
```

### file_recepticle

This program is the recieving end of the file sharing implementation.

The only required argument to this program is where to save the file locally.
This argument should not be a directory path.
It should be a file path.
Also note that the algorithm tries indefinitely to transfer the file even if it doesn't get responses.

Run with the `-h` flag to display the help message which contains all parameters.

Example:
```sh
./demo.sh file_recepticle ../message.txt
```

### send_file

This program is the sending end of the file sharing implementation.

The only required argument is a path to the file to be sent.

Run with the `-h` flag to display the help message which contains all parameters.