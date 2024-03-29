from typing import Any, List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
from utils import *
import json

class Graph:

  def __init__(self, config_file="./src/config.json") -> None:
    self.num_nodes = 0
    self.num_edges = 0
    self.adj = {}
    self.start = []
    self.end = []

    if config_file != None:
              with open(config_file, 'r') as f:
                  self.config_data = json.load(f)


  def add_node(self, node: Any) -> None:
    """
    Adds a node to the graph.

    Parameters:
        node (Any): The node to be added (as a key to a dict)
    """
    try: 
      if self.adj[node] != {}:
        return
    except KeyError:
      self.adj[node] = {}
      self.num_nodes += 1
      
  def add_nodes(self, nodes: List[Any]) -> None:
    """
    Adds a list of nodes to the graph

    Parameters:
        nodes (List[Any]): The list of nodes to be added (as keys to a dict)
    """
    for node in nodes:
      self.add_node(node)
      
  def add_directed_edge(self, u, v, weight):
    """
    Add a directed edge from node 'u' to node 'v' with the specified weight.

    Parameters:
    - u: The source node.
    - v: The target node.
    - weight: The weight of the directed edge.

    If the nodes 'u' and 'v' do not exist in the graph, they are added using the 'add_node' function.
    """
    self.add_node(u)
    self.add_node(v)
    self.adj[u][v] = weight
    self.num_edges += 1
 
  def find_short_path_bpm(self, dijkstra=True) -> list:
        """
        Using dijkstra algorithm or bfs, find the shortest path in the Graph class.
        
        the last red bit is the start, and the last green bit is the end.

        Returns:
        - the nodes path start to end

        """
        paths = []
        if len(self.end) > 5:
            debug("Too many end nodes, may take a while.", "warning")
        
        if len(self.start) == 1:
            start = self.start[0]
            
            def find_path(batch):
                return [self.dijkstra(start, end) for end in batch]

            with ThreadPoolExecutor(max_workers=10) as executor:
                batch_size = 10
                batches = [self.end[i:i + batch_size] for i in range(0, len(self.end), batch_size)]
                paths = [path for batch_paths in executor.map(find_path, batches) for path in batch_paths]

            min_path = min(paths, key=lambda x: x[1])
            return min_path[0]
        
        else:
            for start in self.start:
                if start not in self.adj:
                    debug(f"Start node {start} not in graph", "warning")
                    continue
                
            paths = (self.dijkstra_multiple_pixels(self.start, self.end[0]))


        return paths
            
    
  def add_nodes_and_edges_from_list(self, nodes_list):
      for node in nodes_list:
          x, y, z, color = node

          if color == "red":
              self.start.append(node)
          elif color == "green" and node not in self.end:
              self.end.append(node)

          for other_node in nodes_list:
              if node != other_node:
                  x2, y2, z2, color2 = other_node

                  if color2 != "black" and color != "black" and abs(x - x2) <= 1 and abs(y - y2) <= 1 and not (abs(x - x2) == 1 and abs(y - y2) == 1) and z == z2:
                      weight = 1

                      if color in ["white", "lightgray", "darkgray"] or color2 in ["white", "lightgray", "darkgray"]:
                          weight = 1 if color == "white" or color2 == "white" else self.config_data["graph_config"].get(f"{color}_weight", 1)

                      self.add_directed_edge(node, (x2, y2, z2, color2), weight)

    # Add edges between floors

      nodes = list(self.adj)

      for node1 in nodes:
        x1, y1, z1, color = node1
        
        for node2 in nodes:
            x2, y2, z2, color2 = node2

            # Add this condition to check if x1, y1, and z1, and x2, y2, and z2 are the same
            if x1 == x2 and y1 == y2 and abs(z1 - z2) == 1 and color != "green" and color2 != "green":
                weight = self.config_data["graph_config"].get("between_floors_weight", 1)
                self.add_directed_edge(node1, node2, weight)


  def dijkstra(self, start, end) -> Tuple[List[int], int]:
        """Dijkstra algorithm implementation."""
        
        
        distances: Dict[int, float] = {node: float('infinity') for node in self.adj}
        distances[start] = 0
        visited: set = set()
        
        # Predecessor dictionary to store the previous node in the shortest path
        predecessors: Dict[int, int] = {node: None for node in self.adj}

        while len(visited) < len(self.adj):
            # Select the node with the smallest distance that is not visited
            unvisited_nodes = set(distances.keys()) - visited
            if not unvisited_nodes:
                break

            current_node = min(unvisited_nodes, key=distances.get)
            visited.add(current_node)

            for neighbor, weight in self.adj[current_node].items():
                distance = distances[current_node] + weight

                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    predecessors[neighbor] = current_node

        path: List[int] = []
        current_node = end
        while current_node is not None:
            path.insert(0, current_node)
            current_node = predecessors[current_node]
            
        if path[-1] != end and path[0] != start:
            debug("No path found", "warning")
            return [], 0
          
        total_weight = sum(self.adj[path[i]][path[i + 1]] for i in range(len(path) - 1))

        return path, total_weight
    
  def dijkstra_multiple_pixels(self, starts, end) -> Dict[Tuple[int, int, int, str], List[int]]:
    """Dijkstra algorithm implementation."""
    
    start = starts[0]
    distances: Dict[int, float] = {node: float('infinity') for node in self.adj}
    distances[start] = 0
    visited: set = set()
        
    # Predecessor dictionary to store the previous node in the shortest path
    predecessors: Dict[int, int] = {node: None for node in self.adj}

    while len(visited) < len(self.adj):
        # Select the node with the smallest distance that is not visited
        unvisited_nodes = set(distances.keys()) - visited
        if not unvisited_nodes:
            break

        current_node = min(unvisited_nodes, key=distances.get)
        visited.add(current_node)

        for neighbor, weight in self.adj[current_node].items():
            distance = distances[current_node] + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                predecessors[neighbor] = current_node

        path: List[int] = []
        current_node = end
        while current_node is not None:
            path.insert(0, current_node)
            current_node = predecessors[current_node]

    all_nodes = list(self.adj)

    len_path = len(path)
    for start_pixel in starts:
        if start_pixel != start:
            start_pixel_path = start_pixel
            
            for i in range(1, len_path):
                # Calculate the direction of movement
                
                dx = (path[i][0] - path[i-1][0]) + start_pixel_path[0]
                dy = (path[i][1] - path[i-1][1]) + start_pixel_path[1]
                dz = path[i][2] - path[i-1][2] # if dz is changed, just change the other floors
                
                # Move the start pixel in the same direction
                node_neighboor = (dx, dy, dz)
                
                # try to find the color of the node_neighboor
                for node in all_nodes:
                    if node_neighboor == node[:3]:
                        node_neighboor = node
                        start_pixel_path = node_neighboor
                        path.append(node_neighboor if node_neighboor not in path else path[-1])

    return path









