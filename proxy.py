import argparse
import sys
import socket
import select
import time
from packet_utils import drop_packet, delay_packet
import asyncio
import ipaddress

SERVER = "SERVER"
CLIENT ="CLIENT"

percent_client_drop = 0
percent_client_delay = 0
min_client_delay = 0
max_client_delay = 0

percent_server_drop = 0
percent_server_delay = 0
min_server_delay = 0
max_server_delay = 0

default_diff = 2
server_ip = ""

def check_args():
    parser = argparse.ArgumentParser(description="UDP Proxy for simulating network conditions.")
    parser.add_argument("-cpdrop", type=int, help="Percentage of packets to drop from client to server", default=0)
    parser.add_argument("-cpdelay", type=int, help="Percentage of packets to delay from client to server", default=0)
    parser.add_argument("-cmax", type=int, help="Maximum delay in milliseconds for client packets", default=0)
    parser.add_argument("-cmin", type=int, help="Minimum delay in milliseconds for client packets", default=0)
    parser.add_argument("-spdrop", type=int, help="Percentage of packets to drop from server to client", default=0)
    parser.add_argument("-spdelay", type=int, help="Percentage of packets to delay from server to client", default=0)
    parser.add_argument("-smax", type=int, help="Maximum delay in milliseconds for server packets", default=0)
    parser.add_argument("-smin", type=int, help="Minimum delay in milliseconds for server packets", default=0)
    parser.add_argument("-ip")
    
    args = parser.parse_args()
    global percent_client_drop, percent_client_delay, min_client_delay, max_client_delay
    global percent_server_drop, percent_server_delay, min_server_delay, max_server_delay, server_ip
    
    percent_client_drop = args.cpdrop / 100.0
    percent_client_delay = args.cpdelay / 100.0
    max_client_delay = args.cmax
    min_client_delay = args.cmin
    percent_server_drop = args.spdrop / 100.0
    percent_server_delay = args.spdelay / 100.0
    max_server_delay = args.smax
    min_server_delay = args.smin
    server_ip =  args.ip

    if server_ip == "":
        handle_error("Missing -ip  field")
    elif percent_client_drop < 0 or percent_client_drop > 1:
        handle_error("Client drop percentage must be from 0-100")
    elif percent_server_drop < 0 or percent_server_drop > 1:
        handle_error("Server drop percentage must be from 0-100")
    elif min_client_delay < 0:
        handle_error("Client delay minimum needs to be > 0")
    elif min_server_delay < 0:
        handle_error("Server delay minmium needs to be > 0")
    elif percent_client_delay < 0 or percent_client_delay > 1:
        handle_error("Client delay percentage must be from 0-100")
    elif percent_server_delay < 0 or percent_server_delay > 1:
        handle_error("Server delay percentage must be from 0-100")
    elif min_client_delay > max_client_delay:
        handle_error("Client delay minimum must be bigger than the client delay maximum")
    elif min_server_delay > max_server_delay:
        handle_error("Server delay minimum must be bigger than the server delay minimum")
    elif percent_client_delay == 0 and (min_client_delay != 0 or max_client_delay != 0):
        handle_error("Client delay percentage not set with min or max delays")
    elif percent_server_delay == 0 and (min_server_delay != 0 or max_server_delay != 0):
        handle_error("Server delay percentage not set with min or max delays") 
        
    if percent_client_delay > 0 and min_client_delay == 0 and max_client_delay == 0:
        max_client_delay = default_diff
    if percent_server_delay > 0 and min_server_delay == 0 and max_server_delay == 0:
        max_server_delay = default_diff

def is_ipv4(ip_str):
    try:
        ipaddress.IPv4Address(ip_str)
        return True
    except ipaddress.AddressValueError:
        pass

    try:
        ipaddress.IPv6Address(ip_str)
        return False
    except ipaddress.AddressValueError:
        pass
    err_message = "Invalid IP Address found."
    handle_error(err_message)
    

def forward_data(message, source_address, destination_socket, destination_address):
    """Forwards data from the source to the destination."""
    destination_socket.sendto(message, destination_address)

async def main():
    # Proxy server configuration
    global server_ip
    check_args()
    proxy_host = "::"
    proxy_port = 5173
    server_address = (server_ip, 8080)  # Change to the target server's IP and port
    # Create a UDP socket for the proxy
    proxy_socket = socket.socket((socket.AF_INET6, socket.AF_INET)[is_ipv4(server_ip)], socket.SOCK_DGRAM)
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

                if(drop_packet(percent_client_drop) == False):
                    await delay_packet(percent_client_delay, max_client_delay, min_client_delay, CLIENT)
                    if address not in client_addresses:
                        # Create a new UDP socket for communicating with the server
                        server_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                        client_addresses[address] = (server_socket, server_address)
                        inputs.append(server_socket)
                    
                    # Forward the data to the server
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
                        if drop_packet(percent_server_drop) == False:
                            await delay_packet(percent_server_delay, max_server_delay, min_server_delay, SERVER)
                            proxy_socket.sendto(data, client_address)
                        else:
                            drop_packet(percent_server_drop)
                            print("Drop Packet")
                        
                else:
                    break
def handle_error(err_message):
    print(f"Error: {err_message}")
    exit(1)

if __name__ == '__main__':
    asyncio.run(main())
