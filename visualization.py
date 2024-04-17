import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import datetime

class Graph:
    def __init__(self, title):
        """
        Initialize a new Packet object.

        :param sequence: The sequence number of the packet.
        :param acknowledgment: The acknowledgment number of the packet.
        :param flag: The flag indicating the type/status of the packet (e.g., SYN, ACK).
        """
        self.packets = [0] # packet sent times
        self.start_time = datetime.datetime.now()
        self.title = title
        # ani = FuncAnimation(fig, self.update, interval=1000)  # Update graph every second
        # plt.show()

    def update(self):
        seconds = self.packets  # Extract time in seconds since start
        packet_count = list(range(len(self.packets)))  # Number of packets sent over time
        fig, ax = plt.subplots()
        plt.cla()  # Clear the current axes
        fig.canvas.manager.window.title(self.title)  # Set window title
        
        plt.plot(seconds, packet_count, marker='o')
        plt.xlabel('Time (seconds since start)')
        plt.ylabel('Packets Sent')
        plt.title(self.title)
        #plt.tight_layout()  # Adjust layout to make room for plot elements
        ax.set_xlim(0, None)  # Set minimum x-value to 0
        ax.set_ylim(0, None)  # Set minimum y-value to 0
        

    def add_packet(self):
        current_time = datetime.datetime.now()
        time_diff = (current_time - self.start_time).total_seconds()
        self.packets.append(time_diff)

    def run(self):
        if len(self.packets) > 1:
            self.update()
            plt.show()
            return False
        return True

    def reset(self):
        self.start_time = datetime.datetime.now()
        self.packets = [0]