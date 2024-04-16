import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import datetime

class Graph:
    def __init__(self):
        """
        Initialize a new Packet object.

        :param sequence: The sequence number of the packet.
        :param acknowledgment: The acknowledgment number of the packet.
        :param flag: The flag indicating the type/status of the packet (e.g., SYN, ACK).
        """
        self.packets = [] # packet sent times
        self.start_time = datetime.datetime.now()
        fig, ax = plt.subplots()
        # ani = FuncAnimation(fig, self.update, interval=1000)  # Update graph every second
        # plt.show()

    def update(self, frame):
        seconds = self.packets  # Extract time in seconds since start
        packet_count = list(range(len(self.packets)))  # Number of packets sent over time
        plt.cla()  # Clear the current axes
        if seconds:
            plt.plot(seconds, packet_count, marker='o')
        plt.xlabel('Time (seconds since start)')
        plt.ylabel('Packets Sent')
        plt.title('Packets Sent Over Time')
        plt.tight_layout()  # Adjust layout to make room for plot elements

    def add_packet(self):
        current_time = datetime.datetime.now()
        time_diff = (current_time - self.start_time).total_seconds()
        self.packets.append(time_diff)

    def run(self):
        self.update()
        plt.show()