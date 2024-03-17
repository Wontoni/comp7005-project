import socket
import re
import struct
import pickle


connection = None
server = None
server_host = "::"
server_port = 8080

def main():
    try:
        create_socket()
        bind_socket()
        while True:
            data, address = accept_connection()
            formatted_data = handle_data(data)
            send_message(formatted_data, address)
    except Exception as e:
        handle_error("Failed to receive data from client")

def create_socket():
    try:
        global server
        server = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        print("Server is running...")
    except Exception as e:
        handle_error("Failed to create socket server")

def bind_socket():
    try:
        addr = (server_host, server_port)
        server.bind(addr)
        print('Server binded and waiting for incoming connections...')
    except Exception as e:
        handle_error("Failed to bind to the server")

def accept_connection():
    try:
        while True:
            data, address = server.recvfrom(4) 
            print("Received connection from", address)

            data_size = struct.unpack(">I", data)[0]
            receieved_data = b""
            remaining_data_size = data_size

            if not data_size:
                raise Exception("Failed to receive data")
            
            while remaining_data_size != 0:
                receieved_data += server.recv(remaining_data_size)
                remaining_data_size = data_size - len(receieved_data)
            data = pickle.loads(receieved_data)
            return data, address
    except Exception as e:
        handle_error(e)

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

main()