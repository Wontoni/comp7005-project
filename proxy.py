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
            data, client_address = proxy_socket.recvfrom(4)
            data_size = struct.unpack(">I", data)[0]
            print(f"Received data from {client_address}")
            receieved_data = b""
            remaining_data_size = data_size
            if not data_size:
                raise Exception("Failed to receive data")
            
            while remaining_data_size != 0:
                receieved_data += proxy_socket.recv(remaining_data_size)
                remaining_data_size = data_size - len(receieved_data)

            # Simulate 50% packet drop
            # if random.random() < 0.5:
            #     print("Packet dropped.")
            #     continue  # Do not forward the packet to the server

            # Forward data to the server
            forward_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            forward_socket.sendto(struct.pack(">I", data_size), (server_host, server_port))
            forward_socket.sendto(receieved_data, (server_host, server_port))
            print(f"Forwarded data to server at {server_host}:{server_port}")

            # Wait for response from server
            server_data, _ = forward_socket.recvfrom(4)
            print(f"Received data from {client_address}")
            data_size = struct.unpack(">I", server_data)[0]
            receieved_data = b""
            remaining_data_size = data_size
            if not data_size:
                raise Exception("Failed to receive data")
            
            while remaining_data_size != 0:
                receieved_data += forward_socket.recv(remaining_data_size)
                remaining_data_size = data_size - len(receieved_data)

            # Send response back to client
            proxy_socket.sendto(struct.pack(">I", data_size), client_address)
            proxy_socket.sendto(receieved_data, client_address)
            print("Sent response back to client")

            forward_socket.close()

if __name__ == "__main__":
    main()
