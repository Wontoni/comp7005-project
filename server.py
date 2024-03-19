import socket
import re
import struct
import pickle
import random
from packet import Packet

connection = None
server = None
server_host = "::"
server_port = 8080

last_sequence = -1
acknowledgement = -1

connections = {}
UPPER_SEQUENCE = 9000
LOWER_SEQUENCE = 1000
MAX_DATA = 4096
SYN = "SYN"
ACK = "ACK"
PSH = "PSH"
FIN = "FIN"

def main():
    try:
        create_socket()
        bind_socket()
        while True:
            accept_packet()
            # formatted_data = handle_data(data)
            # send_message(formatted_data, address)
    except Exception as e:
        handle_error("Failed to receive data from client")

def create_socket():
    try:
        global server
        server = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    except Exception as e:
        handle_error("Failed to create socket server")

def bind_socket():
    try:
        addr = (server_host, server_port)
        server.bind(addr)
        print(f'Server is running and waiting for incoming connections on port {server_port}...')
    except Exception as e:
        handle_error("Failed to bind to the server")

def send_message(words, address): 
    try: 
        encoded = pickle.dumps(words)
        server.sendto(struct.pack(">I", len(encoded)), address)
        server.sendto(encoded,address)
    except Exception as e:
        handle_error("Failed to send words")

def handle_data(data):
    words = get_words(data)
    word_count = get_word_count(words)
    char_count = get_char_count(words)
    char_freq = get_char_freq(words)
    sorted_chars = sort_dict(char_freq)
    response = format_response(word_count, char_count, sorted_chars)
    return response

def get_words(word_string):
    formatted_string = remove_whitespace(word_string)
    words = formatted_string.split(" ")
    words = [x for x in words if x]
    return words

def get_word_count(words):
    return len(words)

def remove_whitespace(word_string):
    try:
        return re.sub(' +', ' ', word_string)
    except Exception as e:
        handle_error("Failed to remove whitespaces in data")
        exit(1)

def get_char_count(words):
    count = 0
    for word in words:
        count += len(word)
    return count

def get_char_freq(words):
    char_dict = {}
    words = [word.lower() for word in words]
    words = "".join(words)
    for c in words:
        if c in char_dict:
            char_dict[c] += 1
        else:
            char_dict[c] = 1
    return char_dict

def format_response(word_count, char_count, char_freq):
    response = "Word Count: %d\nCharacter Count: %d\nCharacter Frequencies:"%(word_count, char_count)

    for key, value in char_freq.items():
        response += "\n%s: %d"%(key, value)
    response += "\n"
    return response

def sort_dict(char_freq):
    keys = list(char_freq.keys())
    keys.sort()
    return {i: char_freq[i] for i in keys}

def handle_error(err_message):
    print(f"Error: {err_message}")
    cleanup(False)
    
def cleanup(success):
    if server:
        server.close()
    if success:
        exit(0)
    exit(1)

def send_syn_ack(address):
    if last_sequence < 0:
        handle_error("Invalid sequence number")
    packet = Packet(sequence=last_sequence, acknowledgement=acknowledgement, flags=["SYN", "ACK"])
    send_packet(packet, address)

def send_ack():
    print("SEND ACK")

def send_fin():
    print("SEND FIN")

def receive_fin_ack():
    print("REC FIN ACK")

def check_sequence():
    print("SEQUENCE")

def request_sequence():
    print("CORRECT")

def wait_sequence():
    print("WAIT")

def create_sequence():
    global last_sequence
    try:
        last_sequence = random.randint(LOWER_SEQUENCE, UPPER_SEQUENCE)
    except Exception as e:
        handle_error("Failed to initialize sequence.")

def check_flags(packet, address):
    global last_sequence, acknowledgement
    if SYN in packet.flags:
        create_sequence()
        acknowledgement = packet.sequence + 1
        send_syn_ack(address)
    elif packet.sequence == acknowledgement:
        acknowledgement = packet.sequence + 1
        if ACK in packet.flags and PSH not in packet.flags and FIN not in packet.flags:
            print("RECEIVED AN ACK - CONNECTION HAS OFFICIALY BEEN ESTABLISHED")
        elif ACK in packet.flags and PSH in packet.flags:
            print("RECEIVED ACK PSH - RECEIVED DATA")
        else:
            # last_sequence -= 1 # SHOULD THIS BE DONE?
            print("IMPROPER FLAGS SET IN PACKET")
            print("MAYBE RESEND PACKET?")
    else:
        print("WRONG SEQUENCE FOUND - HANDLE WRONG ORDER")

def send_packet(packet, address):
    global last_sequence
    data = pickle.dumps(packet)
    last_sequence += 1
    server.sendto(data, address)

def accept_packet():
    try:
        data, address = server.recvfrom(MAX_DATA) 
        print("Received packet from", address)
        packet = pickle.loads(data)
        check_flags(packet, address)
    except Exception as e:
        handle_error(e)

main()