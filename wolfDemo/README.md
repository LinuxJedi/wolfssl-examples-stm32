# wolfDemo

The wolfDemo project is an example board intended to be used for demonstrations
of wolfSSL software projects on wolfSSL branded hardware.

It is intended to be easy to pick up and use, with a USB UART chip to program
the board and get logging information. It also has two open standard mikroBus
sockets to expand with thousands of different peripherals.

The following subdirectories exist here:

## wolfDemo_STM32U585

The wolfDemo board KiCad project files.

The board is intended to be manufactured using white PCBs, there is an area on
the rear for JLCPCB QR codes. It is recommended that lead-free HASL is used.

There is also the following associated files:

### `wolfDemo v1 Manual.pdf`

This is an export of the user manual for the board.

### `wolfDemo_backboard.stl`

This is an STL to 3D print the backboard for the wolfDemo board.

It should be printed in white, using supports for the hex holes at the bottom.

The boards are bolted together using M3 7mm bolts and M3 nuts. Five 12.7mm
rubber feet are stuck onto this board to stop it slipping on surfaces it rests
on.

## wolfDemo_ST33

This is a mikroBus click board design for the ST33K TPM chip.

Documentation for this is coming soon.

## examples

All the code examples for the wolfDemo board can be found here.
