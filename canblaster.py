import socket
import time
import can
import datetime
import struct
import argparse

# Settings
bufferSize  = 1024


# Parse arguments
parser = argparse.ArgumentParser(description='Serve local socketcan traffic over UDP')
parser.add_argument('interface', type=str,
                    help='local CAN port, such as can0')
parser.add_argument('-p', '--port', type=int,
                    help='local UDP port to listen on',
                    default=20002)
parser.add_argument('-i', '--bind-ip', type=str,
                    help='IP address to listen on',
                    default='0.0.0.0')

args = parser.parse_args()

print(args)


# Connect to CAN interface
# Future: enable FD frames with CAN_RAW_FD_FRAMES
sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
sock.setblocking(1)
sock.settimeout(0.1)
sock.bind((args.interface,))


#bus = can.Bus(channel='vcan0', interface='socketcan')



# UDP socket for listening for heartbeats of clients
udpserver = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udpserver.setblocking(0) 
udpserver.settimeout(0)
udpserver.bind((args.bind_ip, args.port))


# Multicast socket, broadcast for discovery
multicast_group = ('239.255.43.21', 20000)
multi_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
multi_sock.settimeout(0.2)
ttl = struct.pack('b', 1)
multi_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)


print("canblaster: listening for clients")

# Storage for connected client IP / port tuples as key, heartbeat timestamp as value
clients = {}
status_time = 0
beacon_time = 0
rxcount = 0
txcount = 0

def timestamp():
    now = datetime.datetime.now()
    return now.strftime('%H:%M:%S:')


def send_beacon():

    message = '{"protocol":"CANblaster", "version":1}'
    try:
        # Send data to the multicast group
        sent = multi_sock.sendto(message.encode('utf8'), multicast_group)

    except Exception as e:
        print(type(e), e)

# Listen for incoming UDP packets
while(True):

    # Print status line
    if time.time() - status_time > 5:
        status_time = time.time()
        print(timestamp() + " clients: " + str(len(clients)) + "  rx: " + str(rxcount) + "  tx: " + str(txcount))

    # Broadcast multicast discovery message
    if time.time() - beacon_time > 0.5:
        beacon_time = time.time()
        send_beacon()

    # TODO: Receive either heartbeat message OR CAN message for TX. Differentiate between the two.
    # Probably just no payload msg is heartbeat.
    try:
        bytesAddressPair = udpserver.recvfrom(bufferSize)
        address = bytesAddressPair[1]

        if not address in clients.keys():

            print(timestamp() + " client connected: " + str(address[0]) + ":" + str(address[1]))

        # Set last heartbeat time
        clients[address] = time.time()

    except BlockingIOError as e:
        # If no data ready to receive, just keep processing incoming CAN data
        pass
    
    except ConnectionResetError:
        # Connection interrupted
        pass
        


    # TODO: Receive any CAN messages available
    # Note: this will block for the configured time until data is received

    try:
        res = sock.recvfrom(1024)
        #print(''.join('{:02x}'.format(x) for x in res[0]))
        outframe = res[0]
    except TimeoutError as e:
        continue

    txcount += 1

    #message = bus.recv(0.1)
    #if message is None:
    #    continue
    #else:
    #    print(message)

    # Transmit CAN data to each connected client.
    # List of keys allows us to delete elements while iterating
    for client in list(clients.keys()):
    
        # Send data to client if heartbeat recieved within time
        if time.time() - clients[client] < 1.0:
            #outstr = "CAN Data " + str(time.time()) + "\r\n"
            #udpserver.sendto(outstr.encode('utf8'), client)
            udpserver.sendto(outframe, client)
            
        # Otherwise remove stale client
        else:
            print(timestamp() + " client disconnected: " + str(client[0]) + str(client[1]))
            del clients[client]
            
            
    # TODO: Remove once we are selecting on CAN RX
    time.sleep(0.1)
