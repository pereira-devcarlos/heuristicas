# Graph is a collection of vertices (also called nodes) and edges (connections between the vertices).
graph = {
    # Vertices
    'A': ['B', 'D'],
    'B': ['A', 'C'],
    'C': ['B'],
    'D': ['A']
    # Edge is a connection between two vertices. 
    # Example: An edge between vertex A and vertex B is represented as 'A': ['B'] and 'B': ['A']
}

# Verify Edge
def verify_edge(graph, vertex1, vertex2):
    if vertex1 in graph and vertex2 in graph[vertex1]:
        print(f"Edge exists between {vertex1} and {vertex2}")
    else:
        print(f"Edge does not exist between {vertex1} and {vertex2}")

# Degree of Vertex
def degree_of_vertex(graph, vertex):
    if vertex in graph:
        return len(graph[vertex])
    else:
        return -1  # Vertex does not exist in the graph

def add_edge(graph, vertex1, vertex2):
    if vertex1 in graph and vertex2 in graph:
        graph[vertex1].append(vertex2)
        graph[vertex2].append(vertex1)

def print_graph(graph):
    for vertex, edges in graph.items():
        print(f"{vertex}: {', '.join(edges)}")

verify_edge(graph, 'A', 'B')  # Edge exists
verify_edge(graph, 'A', 'C')  # Edge does not exist

# Verify Degree of Vertex
degree_A = degree_of_vertex(graph, 'A')
print(f"Degree of vertex A: {degree_A}")

degree_B = degree_of_vertex(graph, 'B')
print(f"Degree of vertex B: {degree_B}")

# Adding an edge between A and C
print("\nAdding an edge between A and C...")
add_edge(graph, 'A', 'C')  # Adding an edge between A and C
verify_edge(graph, 'A', 'C')  # Edge now exists

print("\nUpdated Graph:")
print_graph(graph)  # Print the updated graph