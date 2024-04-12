import socket
import select
import time
from packet_utils import drop_packet, delay_packet

def forward_data(message, source_address, destination_socket, destination_address):
    """Forwards data from the source to the destination."""
    destination_socket.sendto(message, destination_address)

def main():
    # Proxy server configuration
    proxy_host = "::"
    proxy_port = 8081
    server_address = ('::1', 8080)  # Change to the target server's IP and port

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

                if(drop_packet(0.4) == False):
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
                        proxy_socket.sendto(data, client_address)
                else:
                    break

if __name__ == '__main__':
    main()
