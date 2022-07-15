import socket
import time
import can
import datetime

# CAN settings
canport = "vcan0"


# Settings
bind_ip     = "127.0.0.1"
bind_port   = 20002
bufferSize  = 1024


# Connect to CAN interface
# Future: enable FD frames with CAN_RAW_FD_FRAMES
sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
sock.setblocking(1)
sock.settimeout(0.1)
sock.bind((canport,))


#bus = can.Bus(channel='vcan0', interface='socketcan')



# Create a datagram socket
udpserver = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udpserver.setblocking(0) 
udpserver.settimeout(0)

# Bind to address and ip
udpserver.bind((bind_ip, bind_port))

print("canblaster: listening for clients")

# Storage for connected client IP / port tuples as key, heartbeat timestamp as value
clients = {}
status_time = 0
rxcount = 0
txcount = 0

def timestamp():
    now = datetime.datetime.now()
    return now.strftime('%H:%M:%S:')

# Listen for incoming UDP packets
while(True):

    if(time.time() - status_time > 5):
        print(timestamp() + " clients: " + str(len(clients)) + "  rx: " + str(rxcount) + "  tx: " + str(txcount))
        status_time = time.time()

    # TODO: Receive either heartbeat message OR CAN message for TX. Differentiate between the two.
    # Probably just no payload msg is heartbeat.
    try:
        bytesAddressPair = udpserver.recvfrom(bufferSize)
        address = bytesAddressPair[1]

        if not address in clients.keys():

            print(timestamp() + " client connected: " + str(address[0]))

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
