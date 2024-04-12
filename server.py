import socket
import re
import struct
import pickle
import random
from packet import Packet
import sys

server = None
server_host = "::"
server_port = 8080

last_sequence = -1
acknowledgement = -1
fourway = False
recieved_packet_list = []
sent_packet_list = []

UPPER_SEQUENCE = 9000
LOWER_SEQUENCE = 1000
MAX_DATA = 4096
SYN = "SYN"
ACK = "ACK"
PSH = "PSH"
FIN = "FIN"

retransmission_time = 5
retransmission_limit = 10
retransmission_attempts = 0

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
    recieved_packet_list.clear()                # cleanup list of recieved packets
    sent_packet_list.clear()                    # cleanup list of sent packets 
    if server:
        server.close()
    if success:
        reset_server()
        main()
        # exit(0)
    exit(1)

def send_syn_ack(address):
    if last_sequence < 0:
        handle_error("Invalid sequence number")
    packet = Packet(sequence=last_sequence, acknowledgement=acknowledgement, flags=["SYN", "ACK"])
    print("SENDING SYN ACK")
    send_packet(packet, address)

def send_ack(destination):
    create_packet(destination_address=destination, flags=[ACK])
    # TRY EXCEPT

def send_fin():
    print("SEND FIN")

def send_fin_ack(destination):
    create_packet(destination_address=destination, flags=[FIN, ACK])

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
    global last_sequence, acknowledgement, fourway
    print(acknowledgement)
    if SYN in packet.flags:
        create_sequence()
        acknowledgement = packet.sequence + 1
        send_syn_ack(address)

    elif is_packet_recieved(packet) == False:                   # checks to see if already in list
        recieved_packet_list.append(packet)                     # if it isnt, it will append
        if packet.sequence == acknowledgement:                  # checks the seq and ack to determine what packet to send
            acknowledgement = packet.sequence + 1
            if ACK in packet.flags and PSH not in packet.flags and FIN not in packet.flags and not fourway:
                print("RECEIVED AN ACK - CONNECTION HAS OFFICIALY BEEN ESTABLISHED")
            elif ACK in packet.flags and PSH in packet.flags: 
                print("RECEIVED ACK PSH - RECEIVED DATA")
                # print(packet.data.decode())
                # packet = pickle.loads(packet.data)
                data = packet.data.decode()
                # print(data)

                if data:
                    send_ack(address)
                else:
                    print("ERROR SEND RETRANSMISSION")
            elif FIN in packet.flags:
                # CHECK CONDITION FOR ENDING - MAYBE
                send_fin_ack(address)
                fourway = True
            elif ACK in packet.flags: # End of fourway - find better way to implement
                print("CLOSING CONNECTION")
                cleanup(True)
            else:
                # last_sequence -= 1 # SHOULD THIS BE DONE?
                print("IMPROPER FLAGS SET IN PACKET")
                print("MAYBE RESEND PACKET?")
        else:
            print("Resend the last packet back to client")

    else:       # if is_packet_recieved == True, send the last packet because if we recieve same packet it means client didnt get the last ack from server
        # print("WRONG SEQUENCE FOUND - HANDLE WRONG ORDER")
        handle_retransmission(address)

def create_packet(destination_address, flags=[], data=b''):
    crafter_packet = Packet(sequence=last_sequence, acknowledgement=acknowledgement, flags=flags, data=data)
    send_packet(crafter_packet, destination_address)

def send_packet(packet, address, is_retransmission=False):
    global last_sequence
    data = pickle.dumps(packet)
    last_sequence += 1

    if is_retransmission:
        server.sendto(data, address)
        print("retransmitting package")
        return

    if is_packet_sent(packet) == False:                     # if the packet has not been sent
        server.sendto(data, address)
        sent_packet_list.append(packet)                     #appending the packet to the sent list
        print(f"Length of sent packet list: {len(sent_packet_list)}")
        print(f"Sending Ack: {packet.acknowledgement}")
        print(f"Sending Seq: {packet.sequence}")
    else:                                                   # if the packet has been sent dont append to list but send the last
        return
        print("out of order stuff")
        

def get_last_sent_packet():
    return sent_packet_list[-1]

"""
Checks to see if the server has already recieved incoming packet
"""
def is_packet_recieved(packet):
    if len(recieved_packet_list) == 0:
        return False
    
    last_packet = recieved_packet_list[-1]
    if last_packet.sequence != packet.sequence:
        return False
    
    if last_packet.sequence == packet.sequence:
        print("Server Recieved Duplicate Packets")
        return True
    
"""
after recieving a retransmisstion from client, server handles it
by sending the last packet.
"""
def handle_retransmission(address):
    last_packet = get_last_sent_packet()
    print('Retransmitting packet')
    send_packet(last_packet, address, True)

"""
Checks to see if the server has already sent the packet
"""
def is_packet_sent(packet):
    if len(sent_packet_list) == 0:
        print("Packet not sent yet")
        return False
    
    last_packet = sent_packet_list[-1]
    if last_packet.acknowledgement >= packet.acknowledgement:
        print("Packets already been sent")
        return True
    
    if last_packet.acknowledgement < packet.acknowledgement:
        print("Packet has not been sent")
        return False

def accept_packet():
    try:
        data, address = server.recvfrom(MAX_DATA) 
        print("Received packet from", address)
        packet = pickle.loads(data)
        print(packet.flags)
        check_flags(packet, address)
        print(f"Recieved Ack: {packet.acknowledgement}")
        print(f"Recieved Seq: {packet.sequence}")
        is_packet_recieved(packet)
        print(f"Length of recieved packet list: {len(recieved_packet_list)}")
    except Exception as e:
        handle_error(e)

def reset_server():
    global server, last_sequence, acknowledgement, fourway, recieved_packet_list, sent_packet_list
    server = None

    last_sequence = -1
    acknowledgement = -1
    fourway = False
    recieved_packet_list = []
    sent_packet_list = []
main()



# IF it is already existing, that means we need to resend the ack packet to the client.


# ? Server handle retransmissions
