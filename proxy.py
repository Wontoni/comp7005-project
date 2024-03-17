import socket
import random
import struct
import pickle

# Proxy server configuration
proxy_host = "::"  # Listening on all IPv6 addresses
proxy_port = 8081  # Port number for the proxy server to listen on

# Destination server configuration
server_host = "::1"  # The IPv6 address of the destination server
server_port = 8080  # The port number of the destination server

def main():
    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as proxy_socket:
        proxy_socket.bind((proxy_host, proxy_port))
        print(f"Proxy server running and listening on port {proxy_port}...")

        while True:
            data, client_address = proxy_socket.recvfrom(4096)
            print(f"Received data from {client_address}")

            # Simulate 50% packet drop
            # if random.random() < 0.5:
            #     print("Packet dropped.")
            #     continue  # Do not forward the packet to the server

            # Forward data to the server
            forward_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            forward_socket.sendto(data, (server_host, server_port))
            print(f"Forwarded data to server at {server_host}:{server_port}")

            # Wait for response from server
            server_data, _ = forward_socket.recvfrom(4096)
            print("Received response from server")

            # Send response back to client
            proxy_socket.sendto(server_data, client_address)
            print("Sent response back to client")

            forward_socket.close()

if __name__ == "__main__":
    main()
