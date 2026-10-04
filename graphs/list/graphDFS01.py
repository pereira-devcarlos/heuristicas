graph = {
    'A': ['B', 'C'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B'],
    'E': ['B', 'F'],
    'F': ['C', 'E']
}


visited = set()

# DFS recursive method
# Pre-Order
def dfsPre(graph, start, visited):
    if start not in graph:
        print(f"Vertex '{start}' don't exist in the graph", end='')
        return
    
    print(start, end=' ')
    visited.add(start)
    
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfsPre(graph, neighbor, visited)

# Post-Order
def dfsPost(graph, start, visited):
    if start not in graph:
        print(f"Vertex '{start}' don't exist in the graph", end='')
        return

    visited.add(start)
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfsPost(graph, neighbor, visited)
    print(start, end=' ')

print("------- Death First Search ---------")
print("Pre-Order:")
dfsPre(graph, 'A', visited)
print()

visited.clear()

print(f"\nPost-Order:")
dfsPost(graph, 'A', visited)
print()