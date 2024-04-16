import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

# Simulate packet logs
# Format: (source, destination, packet_size)
packet_logs = [
    ('Client', 'Server', 250),
    ('Server', 'Client', 300),
    ('Client', 'Server', 200),
    ('Server', 'Client', 310),
    ('Client', 'Server', 220),
    ('Server', 'Client', 290),
    ('Client', 'Server', 230),
]

# Function to create and visualize the graph
def visualize_traffic(packet_logs):
    # Create a directed graph
    G = nx.DiGraph()

    # A dictionary to count packets between pairs
    traffic = defaultdict(int)

    # Sum packet sizes between each pair
    for src, dst, size in packet_logs:
        traffic[(src, dst)] += size
        G.add_node(src)
        G.add_node(dst)

    # Add edges with traffic as weight
    for (src, dst), total_size in traffic.items():
        G.add_edge(src, dst, weight=total_size)

    # Position nodes
    pos = {'Client': (0, 0), 'Server': (1, 0)}

    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color='skyblue')

    # Draw the node labels
    nx.draw_networkx_labels(G, pos)

    # Draw the edges with varying width based on the traffic size
    edge_widths = [G[u][v]['weight'] / 100 for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, width=edge_widths, arrowstyle='-|>', arrowsize=20)

    # Add labels to edges to show the packet sizes
    edge_labels = {(u, v): f'{d["weight"]} bytes' for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # Set plot title and turn off the axis
    plt.title('Network Traffic Visualization')
    plt.axis('off')
    
    # Show the graph
    plt.show()

# Call the function with the packet logs
visualize_traffic(packet_logs)
