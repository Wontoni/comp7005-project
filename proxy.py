import argparse
import sys
import socket
import select
import time
from packet_utils import drop_packet, delay_packet


percent_client_drop = 0
percent_client_delay = 0
min_client_delay = 0
max_client_delay = 0

percent_server_drop = 0
percent_server_delay = 0
min_server_delay = 0
max_server_delay = 0

def check_args(args):
    try:
        global percent_client_delay, percent_client_drop, min_client_delay, max_client_delay, percent_server_delay, percent_server_drop, min_server_delay, max_server_delay
        parser = argparse.ArgumentParser()
        parser.add_argument("-cpdrop")
        parser.add_argument("-cpdelay")
        parser.add_argument("-cmax")
        parser.add_argument("-cmin")
        parser.add_argument("-spdrop")
        parser.add_argument("-spdelay")
        parser.add_argument("-smax")
        parser.add_argument("-smin")
        
        args = parser.parse_args()
        if args.cpdrop:
            check_int(args.cpdrop)
            percent_client_drop = int(args.cpdrop)

        if args.cpdelay:
            check_int(args.cpdelay)
            percent_client_delay = int(args.cpdelay)

        if args.cmax:
            check_int(args.cmax)
            max_client_delay = int(args.cmax)

        if args.cmin:
            check_int(args.cmin)
            min_client_delay = int(args.cmin)
        
        if args.spdrop:
            check_int(args.spdrop)
            percent_server_drop = int(args.spdrop)

        if args.spdelay:
            check_int(args.spdelay)
            percent_server_delay = int(args.spdelay)

        if args.smax:
            check_int(args.smax)
            max_server_delay = int(args.smax)

        if args.smin:
            check_int(args.smin)
            min_server_delay = int(args.smin)


    except Exception as e:
        # handle_error(e)
        exit(1)

def check_int(argument):
    if not argument.isnumeric() or int(argument) > 100 or int(argument) < 0:
        raise Exception(f"{argument} must be a number between 0-100")

def forward_data(message, source_address, destination_socket, destination_address):
    """Forwards data from the source to the destination."""
    destination_socket.sendto(message, destination_address)

def main():
    # Proxy server configuration
    proxy_host = "::"
    proxy_port = 8081
    server_address = ('::1', 8080)  # Change to the target server's IP and port

    check_args(sys.argv)
    # Create a UDP socket for the proxy
    proxy_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    proxy_socket.bind((proxy_host, proxy_port))

    print(f"[*] Listening for UDP traffic on {proxy_host}:{proxy_port}")

    # Sockets from which we expect to read (in this case, only one)
    inputs = [proxy_socket]

    # Client addresses and their corresponding server sockets
    client_addresses = {}

    while True:
        readable, writable, exceptional = select.select(inputs, [], inputs, 0.1)

        for s in readable:
            if s is proxy_socket:
                # Receive data from a client
                data, address = s.recvfrom(4096)
                print(f"[*] Received data from {address}")

                if(drop_packet(0) == False):
                    if address not in client_addresses:
                        # Create a new UDP socket for communicating with the server
                        server_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                        client_addresses[address] = (server_socket, server_address)
                        inputs.append(server_socket)
                    
                    # Forward the data to the server
                    # time.sleep(2)
                    forward_data(data, address, *client_addresses[address])
                else:
                    print("Dropped packet")

        for s in exceptional:
            print(f"[*] Exceptional condition on {s}")
            inputs.remove(s)
            s.close()

        # Check if any server sockets have data to forward back to the client
        for client_address, (server_socket, server_address) in client_addresses.items():
            while True:
                ready = select.select([server_socket], [], [], 0.1)[0]
                if ready:
                    data, _ = server_socket.recvfrom(4096)
                    # do the drop and delay here
                    if data:
                        if drop_packet(0.5) == False:
                            proxy_socket.sendto(data, client_address)
                        else:
                            print("Packet dropped from server")
                else:
                    break

if __name__ == '__main__':
    main()
