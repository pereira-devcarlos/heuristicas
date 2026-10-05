import time

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
        if first_v == second_v or not self.graph.has_edge(first_v, second_v):
            return False
        
        visited.add(first_v)
        visited.add(second_v)

        for u, v in self.best_solution[1:]:
            if u != second_v or v in visited or not self.graph.has_edge(u, v):
                return False
            visited.add(v)
            second_v = v
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

    def local(self, solution=None):
        """
        Local search heuristic.
        """
        print("Executing local search algorithm...")

        if solution is not None:
            self.best_solution = solution.copy()

        if not self.best_solution:
            self.construtiva()

        path = self._valid_path_prefix(self.best_solution)
        if not path:
            self.construtiva()
            path = self._valid_path_prefix(self.best_solution)
            if not path:
                return self.best_solution

        while True:
            best_move = None
            best_gain = 0

            visited = set(path)

            # Extend either endpoint with an unvisited neighbor.
            for endpoint_index in (0, -1):
                endpoint = path[endpoint_index]
                for neighbor in self.graph.neighbors(endpoint):
                    if neighbor in visited:
                        continue

                    gain = self.graph[endpoint][neighbor]["weight"]
                    if gain > best_gain:
                        best_gain = gain
                        best_move = ("extend", endpoint_index, neighbor)

            # Replace one path edge u-v by u-x-v.
            for edge_index, (origin, destination) in enumerate(zip(path, path[1:])):
                edge_weight = self.graph[origin][destination]["weight"]
                for candidate in self.graph.nodes:
                    if candidate in visited:
                        continue
                    if not self.graph.has_edge(origin, candidate):
                        continue
                    if not self.graph.has_edge(candidate, destination):
                        continue

                    gain = (
                        self.graph[origin][candidate]["weight"]
                        + self.graph[candidate][destination]["weight"]
                        - edge_weight
                    )
                    if gain > best_gain:
                        best_gain = gain
                        best_move = ("insert", edge_index, candidate)

            if best_move is None:
                break

            move_type, position, vertex = best_move
            if move_type == "extend":
                if position == 0:
                    path.insert(0, vertex)
                else:
                    path.append(vertex)
            else:
                path.insert(position + 1, vertex)

        self.best_solution = list(zip(path, path[1:]))
        return self.best_solution

    def _valid_path_prefix(self, solution):
        """Return the longest valid simple path prefix of an edge solution."""
        if not solution:
            return []

        first_origin, first_destination = solution[0]
        if first_origin == first_destination or not self.graph.has_edge(first_origin, first_destination):
            return []

        path = [first_origin, first_destination]
        for origin, destination in solution[1:]:
            if origin != path[-1] or destination in path:
                break
            if not self.graph.has_edge(origin, destination):
                break
            path.append(destination)
        return path

    def vnd(self):
            """
            Variable Neighborhood Descent (VND) algorithm.
            """
            print("Executing VND algorithm...")
            start_time = time.time()
            max_time = 30  # Tempo máximo de 30 segundos como critério de parada

            # Garante uma solução inicial utilizando a heurística construtiva das aulas passadas
            if not self.best_solution:
                self.construtiva()

            # Obtém o prefixo de caminho simples válido
            path = self._valid_path_prefix(self.best_solution)
            if not path:
                self.construtiva()
                path = self._valid_path_prefix(self.best_solution)
                if not path:
                    return self.best_solution

            k = 1
            # Loop do VND: continua até esgotar as vizinhanças (k > 2) ou ultrapassar 30 segundos
            while k <= 2 and (time.time() - start_time) < max_time:
                best_move = None
                best_gain = 0
                visited = set(path)

                if k == 1:
                    # N1: Vizinhança de Extensão (Extend either endpoint)
                    for endpoint_index in (0, -1):
                        endpoint = path[endpoint_index]
                        for neighbor in self.graph.neighbors(endpoint):
                            if neighbor in visited:
                                continue

                            gain = self.graph[endpoint][neighbor]["weight"]
                            if gain > best_gain:
                                best_gain = gain
                                best_move = ("extend", endpoint_index, neighbor)

                elif k == 2:
                    # N2: Vizinhança de Inserção (Replace one path edge u-v by u-x-v)
                    for edge_index, (origin, destination) in enumerate(zip(path, path[1:])):
                        edge_weight = self.graph[origin][destination]["weight"]
                        for candidate in self.graph.nodes:
                            if candidate in visited:
                                continue
                            if not self.graph.has_edge(origin, candidate):
                                continue
                            if not self.graph.has_edge(candidate, destination):
                                continue

                            gain = (
                                self.graph[origin][candidate]["weight"]
                                + self.graph[candidate][destination]["weight"]
                                - edge_weight
                            )
                            if gain > best_gain:
                                best_gain = gain
                                best_move = ("insert", edge_index, candidate)

                # Avalia se houve alguma melhoria
                if best_move is not None:
                    move_type, position, vertex = best_move
                    if move_type == "extend":
                        if position == 0:
                            path.insert(0, vertex)
                        else:
                            path.append(vertex)
                    else:
                        path.insert(position + 1, vertex)
                    
                    # Se melhorou, retorna para a primeira vizinhança
                    k = 1
                else:
                    # Se não houve melhora (ótimo local nesta vizinhança), avança para a próxima
                    k += 1

            # Atualiza a melhor solução convertendo a sequência de vértices em lista de arestas
            self.best_solution = list(zip(path, path[1:]))
            return self.best_solution

    def evaluate(self):
        """
        Evaluate the solution.
        """
        cost = 0
        for u, v in self.best_solution:
            cost += self.graph[u][v]['weight']

        return cost 