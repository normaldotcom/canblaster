import json
import socket
import time
import struct
import json
import select


class CANBlasterClient(object):

    def __init__(self):
        self.found_server = False
        self.server_ip = ''

        multicast_group = '239.255.43.21'
        server_address = ('', 20000)

        # Socket for tx/rx to server via UDP Unicast
        self.unicast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        self.unicast_sock.settimeout(0.1)

        # Create the socket for multicast RX
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind to the server address
        sock.bind(server_address)
        group = socket.inet_aton(multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        start_time = time.time()
        print("Begin server detection...")

        while True:
            if(time.time() - start_time > 5.0):
                print("Failed to detect CANblaster server")
                break;

            data, address = sock.recvfrom(1024)
            res = None
            try:
                res = json.loads(data)
            except Exception as e:
                print("Invalid message received, skipping")
                continue

            if res['protocol'] == 'CANblaster':
                print("Found CANblaster server at " + str(address))

                if res['version'] == 1:
                    print("Version check: OK")
                    self.server_ip = address
                    self.found_server = True
                    return



    def heartbeat(self):

        print(self.server_ip)
        # Let server know we are here
        print("Send heartbeat to ", self.server_ip)
        self.unicast_sock.sendto(bytes('127.0.0.1', "utf-8"), (self.server_ip[0], 20002))

    def rx(self):
        #ready = select.select([self.unicast_sock], [], [], 0.1) #timeout seconds
        #if ready[0]:
        try:
            data, address = self.unicast_sock.recvfrom(4096)
            print(data, address)
            return data
        except TimeoutError as e:
            return None





# TEST CODE ##########################


b = CANBlasterClient()
last_heartbeat = time.time()
while True:
    if(time.time() - last_heartbeat > 1.0):
        last_heartbeat = time.time()
        b.heartbeat();

    b.rx()

    time.sleep(0.01)



#b.listen()
