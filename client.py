import socket
import sys
import ipaddress
import struct
import pickle
import random
from packet import Packet

retransmission_time = 2
waiting_state_time = 5
retransmission_limit = 999

# Change to ipv4 for connection via IPv4 Address or ipv6 for IPv6
server_port = 5173


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
packets_received = []
last_sequence = -1
expected_sequence = -1
acknowledgement = -1

processed_data=''

retransimssion_attempts = 0
is_threeway = False
is_fourway = False
connection_established = False

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
        client.connect((server_host, server_port))
        three_handshake()
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
    if client:
        print("Closing Connection")
        client.close()
    if success:
        exit(0)
    exit(1)

def three_handshake():
    global is_threeway, connection_established
    create_sequence()
    send_syn()
    accept_packet() # SYN ACK
    is_threeway = True
    send_ack()
    three_handshake_part_two()

def three_handshake_part_two():
    global is_threeway, connection_established
    while True:
        success = waiting_state()
        if success:
            break
    is_threeway = False
    connection_established = True
    transmit_data()

def four_handshake():
    global is_fourway, last_sequence, acknowledgement
    print("Fourway Handshake started")
    send_fin_ack()
    accept_packet()
    send_ack()
    is_fourway = True
    while True:
        success = waiting_state()
        if success:
            break
    is_fourway = False
    cleanup(True)

def waiting_state():
    print("WAITING STATE")
    success = accept_packet()
    if success:
        return True
    
    #acknowledgement -= 1
    handle_retransmission()
    

def transmit_data():
    try:
        data = processed_data.encode() #pickle.dumps(processed_data)

        # Split data into chunks
        chunk_size = MAX_DATA - MAX_HEADER
        chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
        for chunk in chunks:
            send_ack_psh(chunk)
            accept_packet()

        # DATA SHOULD BE DONE TRANSMITTING
        four_handshake()
    except Exception as e:
        handle_error(e)

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
    print(f"Sending {packet.flags}")
    client.sendall(data)

def accept_packet():
    try:
        global retransmission_time, retransimssion_attempts, waiting_state_time
        if is_fourway or is_threeway:
            client.settimeout(waiting_state_time)
        else:
            client.settimeout(retransmission_time)
        data, address = client.recvfrom(MAX_DATA) 
        print("Received packet from", address)
        packet = pickle.loads(data)
        print(packet.flags)
        packets_received.append(packet)
        retransimssion_attempts = 0
        check_flags(packet)
    except socket.timeout as e:
        if is_threeway or is_fourway:
            return True
        handle_retransmission()
    except Exception as e:
        print(e)

def handle_retransmission():
        global retransimssion_attempts, retransmission_limit, last_sequence
        if retransimssion_attempts >= retransmission_limit:
            # ! Force close a connection
            print("MAX RETRANSMISSIONS HIT")
            cleanup(False)
        last_packet_sent = packets_sent.pop()
        last_sequence -= 1
        retransimssion_attempts += 1
        print(f"Retransmitting {last_packet_sent.flags}")
        send_packet(last_packet_sent)
        accept_packet()

def check_flags(packet):
    global last_sequence, acknowledgement, is_threeway, connection_established
    # if SYN in packet.flags and ACK in packet.flags:
    #     last_sequence = packet.acknowledgement
    #     acknowledgement = packet.sequence + 1
    #     print("RECEIVED A SYN ACK")
    #     return
    #     # send_ack()
    #     # transmit_data()
    if packet.sequence == acknowledgement and not is_threeway:
        print(f"Received {packet.flags}")
        acknowledgement = packet.sequence + 1
        if PSH not in packet.flags and FIN not in packet.flags:
            return
        elif PSH in packet.flags:
            return
        elif FIN in packet.flags:
            return
        else:
            handle_error("Bad flags received")
    elif SYN in packet.flags and ACK in packet.flags and not connection_established:
        last_sequence = packet.acknowledgement
        acknowledgement = packet.sequence + 1
        print("RECEIVED SYN ACK")
        return
    else:
        # print(f"I Received sequence      {packet.sequence}")
        # print(f"I was expecting sequence {acknowledgement}")
        if packet.flags == [SYN, ACK]:
            packets_sent.pop()
            last_sequence -= 1
            is_threeway = True
            connection_established = False
            handle_retransmission()
            three_handshake_part_two()
            return
            #last_sequence -= 1
            # HERE
            # return
        handle_retransmission()

def send_syn():
    create_packet(flags=[SYN])

def send_ack_psh(data):
    create_packet(flags=[ACK, PSH], data=data)

def send_ack():
    create_packet(flags=[ACK])

def send_fin_ack():
    create_packet(flags=[FIN, ACK])

def check_packet_received(packet):
    global packets_received, packets_sent
    if packet not in packets_received:
        packets_received.append(packet)
    else:
        # PACKET IS ALREADY RECEIVED, SOMETHING DROPPED ALONG THE WAY
        if packet.sequence == packets_received[-1].sequence + 1:
            return # Nothin else should be done
        elif packet.sequence > packets_received[-1].sequence + 1:
            handle_retransmission() # Resend the last packet sent
            return
        else:
            for packet in packets_received:
                print(1) #if packet.sequence 


if __name__ == "__main__":
    main()