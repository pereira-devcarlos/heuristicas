class Heuristics:
    def __init__(self, instance_data):
        """
        Initialize the Heuristics class with the instance data.
        """
        self.graph = instance_data
        # A solution is represented as a list of edges, where each edge is an ordered pair of nodes (u, v).
        self.best_solution: list[tuple[int, int]] = []

    def construtiva(self):
        """
        Constructive heuristic.
        """
        print("Executing construtiva algorithm...")
        self.best_solution = []

        # Smallest degree
        smallVertex = None
        smallDegree = float("inf")

        # Find the vertex with the smallest degree
        for vertex in self.graph.nodes:
            degree = self.graph.degree[vertex]

            if degree < smallDegree:
                smallDegree = degree
                smallVertex = vertex

        # Start the path from the vertex with the smallest degree
        current = smallVertex
        visited = set()
        visited.add(current)

        while True:
            # Biggest neighbor
            bestNeighbor = None
            highestDegree = float("-inf")

            # Find the neighbor with the highest degree
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    degree = self.graph.degree[neighbor]

                    if degree > highestDegree:
                        highestDegree = degree
                        bestNeighbor = neighbor

            # If no unvisited neighbor is found, break the loop
            if bestNeighbor is None:
                break;

            # Add the edge to the best solution and mark the neighbor as visited
            self.best_solution.append((current, bestNeighbor))
            visited.add(bestNeighbor)
            current = bestNeighbor

    def local(self):
        """
        Local search heuristic.
        """
        pass

    def evaluate(self):
        """
        Evaluate the solution.
        """
        cost = 0
        for u, v in self.best_solution:
            cost += self.graph[u][v]['weight']

        return cost 
