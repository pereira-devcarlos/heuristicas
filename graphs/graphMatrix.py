# Matrix Representation of a Graph
graph = [
    # Vertices: A, B, C, D
    # Adjacency Matrix
    [0, 1, 0, 1],  # A is connected to B and D
    [1, 0, 1, 0],  # B is connected to A and C
    [0, 1, 0, 0],  # C is connected to B
    [1, 0, 0, 0]   # D is connected to A
]
# Index map for vertices
index_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}

# Verify Edge
def verify_edge(graph, vertex1, vertex2):
    if vertex1 in index_map and vertex2 in index_map:
        i = index_map[vertex1]
        j = index_map[vertex2]
        if graph[i][j] == 1:
            print(f"Edge exists between {vertex1} and {vertex2}")
        else:
            print(f"Edge does not exist between {vertex1} and {vertex2}")
    else:
        print("One or both vertices do not exist in the graph")

def degree_of_vertex(graph, vertex):
    if vertex in index_map:
        i = index_map[vertex]
        return sum(graph[i])  # Count the number of edges connected to the vertex
    else:
        return -1  # Vertex does not exist in the graph


# Testing the functions
print("---------------- Edges of the Graph -----------------")
verify_edge(graph, 'A', 'B')  # Edge exists
verify_edge(graph, 'A', 'C')  # Edge does not exist
verify_edge(graph, 'A', 'E')  # One or both vertices do not exist

print(f"\n----------------- Degree of Vertex -------------------")
degree_A = degree_of_vertex(graph, 'A')
if degree_A != -1:
    print(f"Degree of vertex A: {degree_A}")
else:
    print("Vertex A does not exist in the graph")

degree_C = degree_of_vertex(graph, 'C')
if degree_C != -1:
    print(f"Degree of vertex C: {degree_C}")
else:
    print("Vertex C does not exist in the graph")

degree_E = degree_of_vertex(graph, 'E')
if degree_E != -1:
    print(f"Degree of vertex E: {degree_E}")
else:
    print("Vertex E does not exist in the graph")
