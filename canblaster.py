import socket
import time
import datetime
import struct
import argparse


class CANblaster(object):

    def __init__(self, can_interface, bind_port, bind_ip, bind_ttl, beaconrate, clienttimeout):

        # Connect to CAN interface
        # Future: enable FD frames with CAN_RAW_FD_FRAMES
        self.can_socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self.can_socket.setblocking(1)
        self.can_socket.settimeout(0.1)
        self.can_socket.bind((can_interface,))


        # UDP socket for listening for heartbeats of clients
        self.udpserver = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.udpserver.setblocking(0)
        self.udpserver.settimeout(0)
        self.udpserver.bind((bind_ip, bind_port))


        # Multicast socket, broadcast for discovery
        self.multicast_group = ('239.255.43.21', 20000)
        self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.multicast_socket.settimeout(0.2)
        ttl = struct.pack('b', bind_ttl)
        self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        self.beacon_rate = beaconrate
        self.client_timeout = clienttimeout

        print("canblaster: listening for clients. Blasting on " + str(bind_ip) + ":" + str(bind_port) + " TTL=" + str(bind_ttl))




    def timestamp(self):
        now = datetime.datetime.now()
        return now.strftime('%H:%M:%S:')


    # Send UDP multicast beacon message for discovery
    def send_beacon(self):

        message = '{"protocol":"CANblaster", "version":1}'
        try:
            # Send data to the multicast group
            sent = self.multicast_socket.sendto(message.encode('utf8'), self.multicast_group)

        except Exception as e:
            print(type(e), e)


    # Start processing/broadcasting of CAN frames. Does not return.
    def begin(self):

        # Storage for connected client IP / port tuples as key, heartbeat timestamp as value
        clients = {}
        status_time = 0
        beacon_time = 0
        rxcount = 0
        txcount = 0


        # Listen for incoming UDP packets
        while(True):

            # Print status line
            if time.time() - status_time > 5:
                status_time = time.time()
                print(self.timestamp() + " clients: " + str(len(clients)) + "  rx: " + str(rxcount) + "  tx: " + str(txcount))

            # Broadcast multicast discovery message
            if time.time() - beacon_time > self.beacon_rate:
                beacon_time = time.time()
                self.send_beacon()

            # TODO: Receive either heartbeat message OR CAN message for TX. Differentiate between the two.
            # Probably just no payload msg is heartbeat.
            try:
                bytesAddressPair = self.udpserver.recvfrom(1024)
                address = bytesAddressPair[1]

                if not address in clients.keys():

                    print(self.timestamp() + " client connected: " + str(address[0]) + ":" + str(address[1]))

                # Set last heartbeat time
                clients[address] = time.time()

            except BlockingIOError as e:
                # If no data ready to receive, just keep processing incoming CAN data
                pass

            except ConnectionResetError:
                # Connection interrupted
                pass


            # Receive any CAN messages available
            try:
                res = self.can_socket.recvfrom(1024)
                outframe = res[0]
            except TimeoutError as e:
                continue

            txcount += 1


            # Transmit CAN data to each connected client.
            # List of keys allows us to delete elements while iterating
            for client in list(clients.keys()):

                # Send data to client if heartbeat recieved within time
                if time.time() - clients[client] < self.client_timeout:
                    #outstr = "CAN Data " + str(time.time()) + "\r\n"
                    #udpserver.sendto(outstr.encode('utf8'), client)
                    try:
                        self.udpserver.sendto(outframe, client)
                    except BlockingIOError as e:
                        print(self.timestamp() + "Dropping packet, network output buffer full")

                # Otherwise remove stale client
                else:
                    print(self.timestamp() + " client disconnected: " + str(client[0]) + str(client[1]))
                    del clients[client]


            # TODO: Remove once we are selecting on CAN RX
            time.sleep(0.001)




if __name__ == "__main__":

    # Parse arguments
    parser = argparse.ArgumentParser(description='Serve local socketcan traffic over UDP')
    parser.add_argument('can_interface', type=str,
                        help='local CAN port, such as can0')
    parser.add_argument('-p', '--port', type=int,
                        help='local UDP port to listen on',
                        default=20002)
    parser.add_argument('-i', '--bind-ip', type=str,
                        help='IP address to listen on',
                        default='0.0.0.0')
    parser.add_argument('-t', '--ttl', type=int,
                        help='TTL for multicast discovery beacon',
                        default=1)
    parser.add_argument('-b', '--beacon-rate', type=float,
                        help='Period in seconds for beacon rate transmission',
                        default=0.25)
    parser.add_argument('-c', '--client-timeout', type=float,
                        help='Timeout for connected clients in seconds',
                        default=5)

    args = parser.parse_args()

    b = CANblaster(args.can_interface, args.port, args.bind_ip, args.ttl, args.beacon_rate, args.client_timeout)
    b.begin()
