import random
import time

def drop_packet(drop_probability):
    return random.random() < drop_probability


def delay_packet(delay_probability, max_delay=5):
    if random.random() < delay_probability:
        print('PACKET STATUS: Delayed...')
        # time.sleep(random.uniform(0, max_delay))
        time.sleep(max_delay)