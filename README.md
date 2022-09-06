# CANblaster
Utility to forward socketcan CAN bus traffic over unreliable links via UDP

## Features

* Auto-discovery via multicast UDP
* Forwarding of standard CAN frames over UDP
* Compatability with [cangaroo](https://github.com/normaldotcom/cangaroo) analyzer software
* Supports multiple clients

## Implementation

* Broadcast multicast UDP frames to announce to any listening applications (such as cangaroo) at configurable rate
* Listening applications broadcast a heartbeat message to CANblaster
* As long as the listening application is transmitting a heartbeat, CANblaster transmits a unicast UDP frame for each CAN message on the bus

## In Progress
* Forwarding of FD frames over UDP (in progress)
* Transmission of CAN frames from rx'ed UDP frames
