import random
import time
import asyncio

def drop_packet(drop_probability):
    return random.random() < drop_probability


async def delay_packet(delay_probability, max_delay=5):
    if random.random() < delay_probability:
        print('Packet Delay Start')
        # time.sleep(random.uniform(0, max_delay))
        await asyncio.sleep(max_delay)
        print('Packet Delay Finish')

