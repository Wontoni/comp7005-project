import socket
import sys
import ipaddress
import struct
import pickle
import random
from packet import Packet

# Variables to change based on server host location

# Change to ipv4 for connection via IPv4 Address or ipv6 for IPv6
server_port = 8081


file_name = None
server_host = None
client = None

UPPER_SEQUENCE = 9000
LOWER_SEQUENCE = 1000
MAX_DATA = 4096
MAX_HEADER = 256
SYN = "SYN"
ACK = "ACK"
PSH = "PSH"
FIN = "FIN"

packets_sent = [] # MAYBE SORT BY SEQUENCE NUMBER? --> Binary search for correct sequence
last_sequence = -1
expected_sequence = -1
acknowledgement = -1

processed_data=''

"""
DROPPED PACKETS
settimeout
- If timed out, nothing was received.

delay packets (max/min)
- % chance to drop currently delayed packets
"""


def main():
    global processed_data
    check_args(sys.argv)
    handle_args(sys.argv)
    processed_data = read_file()

    if processed_data:
        create_socket()
        connect_client()
        # send_message(words)
        # receieve_response()

def check_args(args):
    try:
        if len(args) != 3:
            raise Exception("Invalid number of arguments")
        elif not args[1].endswith('.txt'):
            raise Exception("Invalid file extension, please input a .txt file")
        is_ipv4(args[2]) # Will handle invalid addresses
    except Exception as e:
        handle_error(e)
        exit(1)

def handle_args(args):
    global file_name, server_host
    try:
        file_name = sys.argv[1]
        server_host = sys.argv[2]
    except Exception as e:
        print(e)
        handle_error("Failed to retrieve inputted arguments.")

def create_socket():
    try: 
        global client
        # INET = IPv4 /// INET6 = IPv6
        client = socket.socket((socket.AF_INET6, socket.AF_INET)[is_ipv4(server_host)], socket.SOCK_DGRAM)

    except Exception as e:
        handle_error("Failed to create client socket")

def connect_client():
    try: 
        client.settimeout(10)
        client.connect(('localhost', server_port))
        three_handshake()
        while True:
            accept_packet()
    except Exception as e:
        print(e)
        handle_error(f"Failed to connect to socket with the address and port - {server_host}:{server_port}")

def read_file():
    try:
        with open(file_name, 'r', errors="ignore") as file:
            content = file.read()
            if not content:
                raise Exception("File is empty.")
            formatted_data = replace_new_lines(content)
            return formatted_data
    except FileNotFoundError:
        handle_error(f"File '{file_name}' not found.")
    except Exception as e:
        handle_error(e)

def replace_new_lines(text_data):
    try:
        res = text_data.replace('\n', ' ')
        return res
    except Exception as e:
        handle_error(e)

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
    
def handle_error(err_message):
    print(f"Error: {err_message}")
    cleanup(False)
    
def display_message(message):
    print(f'Received response\n{message}')
    cleanup(True)

def cleanup(success):
    print("CLOSING CONNECTION")
    if client:
        client.close()
    if success:
        exit(0)
    exit(1)

def three_handshake():
    create_sequence()
    create_packet([SYN])
    accept_packet()
    create_packet([ACK])

def transmit_data():
    try:
        data = pickle.dumps(processed_data)

        # Split data into chunks
        chunk_size = MAX_DATA - MAX_HEADER
        chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
        for chunk in chunks:
            create_packet(flags=[ACK, PSH], data=chunk)
            accept_packet()

        # DATA SHOULD BE DONE TRANSMITTING
        four_handshake()
    except Exception as e:
        handle_error(e)

def four_handshake():
    print("STARTING FOURWAY HANDSHAKE")
    create_packet([FIN])
    accept_packet()
    create_packet([ACK])
    for packet in packets_sent:
        packet.display_info()
    cleanup(True)

def create_packet(flags=[], data=b''):
    crafter_packet = Packet(sequence=last_sequence, acknowledgement=acknowledgement, flags=flags, data=data)
    send_packet(crafter_packet)

def create_sequence():
    global last_sequence
    last_sequence = random.randint(LOWER_SEQUENCE, UPPER_SEQUENCE)

def send_sequence_packet():
    print("SEND SEQUENCE PACKET")

def send_packet(packet):
    global last_sequence, packets_sent
    packets_sent.append(packet)
    last_sequence += 1
    data = pickle.dumps(packet)
    client.sendall(data)

def accept_packet():
    data, address = client.recvfrom(MAX_DATA) 
    print("Received packet from", address)
    packet = pickle.loads(data)
    check_flags(packet)

def check_flags(packet):
    global last_sequence, acknowledgement
    if SYN in packet.flags and ACK in packet.flags:
        last_sequence = packet.acknowledgement
        acknowledgement = packet.sequence + 1
        print("RECEIVED A SYN ACK")
        create_packet([ACK])
        transmit_data()
    elif ACK in packet.flags:
        if packet.sequence == acknowledgement:
            acknowledgement = packet.sequence + 1
            if PSH not in packet.flags:
                print("RECEIVED AN ACK")
            elif PSH in packet.flags:
                print("RECEIVED ACK PSH - RECEIVED DATA")
            else:
                print("IMPROPER FLAGS SET IN PACKET")
                print("MAYBE RESEND PACKET?") # RESET/FIN
        else:
            print("WRONG ORDER - FIX SEQUENCE")
    else:
        print("MISSING AN ACK")


if __name__ == "__main__":
    main()