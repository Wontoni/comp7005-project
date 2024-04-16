import random
import time
import asyncio

def drop_packet(drop_probability):
    return random.random() < drop_probability


async def delay_packet(delay_probability, max_delay, min_delay, origin):
    if random.random() < delay_probability:
        delay_duration = random.uniform(min_delay, max_delay)
        print(f'[{origin}] Packet Delay Start')
        await asyncio.sleep(delay_duration)
        print(f'[{origin}] Packet Delay Finish')

