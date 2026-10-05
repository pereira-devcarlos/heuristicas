class Heuristics:
    def __init__(self, instance_data):
        """
        Initialize the Heuristics class with the instance data.
        """
        self.graph = instance_data
        # A solution is represented as a list of edges, where each edge is an ordered pair of nodes (u, v).
        self.best_solution: list[tuple[int, int]] = []

    def construtiva(self, solution=None):
        """
        Constructive heuristic.
        """
        print("Executing construtiva algorithm...")
        visited = set()

        if solution is None:
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
            visited.add(current)
        else:
            # Continue from the valid prefix already in the solution.
            self.best_solution = solution.copy()
            current = self.best_solution[-1][1]

            for u, v in self.best_solution:
                visited.add(u)
                visited.add(v)

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

    def is_valid(self):
        """
        Check if the current best solution is valid.
        """
        visited = set()

        if not self.best_solution:
            return False

        first_v, second_v = self.best_solution[0]
        if first_v == second_v:
            return False
        
        visited.add(first_v)
        visited.add(second_v)

        for u, v in self.best_solution[1:]:
            if v in visited:
                return False
            visited.add(v)
        return True

    def repair(self):
        """
        Repair heuristic.
        """
        print("Executing repair algorithm...")

        while self.best_solution and not self.is_valid():
            self.best_solution.pop()

        if self.best_solution:
            self.construtiva(self.best_solution)

    def local(self):
        """
        Local search heuristic.
        """
        print("Executing local search algorithm...")

    def evaluate(self):
        """
        Evaluate the solution.
        """
        cost = 0
        for u, v in self.best_solution:
            cost += self.graph[u][v]['weight']

        return cost 