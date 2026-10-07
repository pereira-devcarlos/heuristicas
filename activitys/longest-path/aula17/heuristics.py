import time
import random

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

    def perturbation(self, path):
        """
        Perturbation mechanism for the ILS.
        Removes a contiguous subpath of random length from a random position.
        """
        if len(path) <= 3:
            return path.copy()

        # Decide quantos vértices remover (por exemplo, entre 2 e 4 vértices, se possível)
        num_remove = random.randint(2, min(4, len(path) - 2))
        
        # Escolhe um ponto de início aleatório para a remoção
        # Evitamos remover os extremos absolutos para tentar manter alguma estrutura
        start_remove = random.randint(1, len(path) - num_remove - 1)
        
        # Cria o novo caminho excluindo a parte selecionada
        new_path = path[:start_remove] + path[start_remove + num_remove:]
        
        # Importante: Ao remover vértices do meio, o caminho pode deixar de ser contíguo 
        # (a aresta entre a parte anterior e a posterior pode não existir).
        # Precisamos garantir que o caminho retornado seja válido.
        valid_path = [new_path[0]]
        for i in range(1, len(new_path)):
            if self.graph.has_edge(valid_path[-1], new_path[i]):
                valid_path.append(new_path[i])
            else:
                break # Quebra a validade do caminho, paramos aqui.

        return valid_path

    def ils(self):
        """
        Iterated Local Search (ILS) algorithm.
        """
        print("Executing ILS algorithm...")
        start_time = time.time()
        max_time = 30  # Tempo máximo de 30 segundos como critério de parada

        # 1. Gera solução inicial (S0)
        self.construtiva()
        
        # 2. Refina a solução inicial com a busca local (S*)
        self.local()
        
        # Salva o melhor caminho e o melhor custo global encontrados
        best_global_path = self._valid_path_prefix(self.best_solution)
        best_global_cost = self.evaluate()

        # Loop principal do ILS até o tempo acabar
        while (time.time() - start_time) < max_time:
            
            # 3. Perturbação: aplica sobre o melhor caminho atual (S')
            perturbed_path = self.perturbation(best_global_path)
            
            # Converte a sequência de vértices perturbada de volta para lista de arestas
            self.best_solution = list(zip(perturbed_path, perturbed_path[1:]))
            
            # 4. Busca Local: aplica a busca local na solução perturbada (S*')
            # (Note que self.local() atualiza self.best_solution internamente)
            self.local()
            
            # 5. Critério de Aceitação
            current_cost = self.evaluate()
            
            # Se a nova solução otimizada for melhor que a global, atualiza
            if current_cost > best_global_cost:
                best_global_cost = current_cost
                best_global_path = self._valid_path_prefix(self.best_solution)

        # Ao final do tempo, garante que a melhor solução global encontrada seja mantida
        self.best_solution = list(zip(best_global_path, best_global_path[1:]))
        return self.best_solution

    def evaluate(self):
        """
        Evaluate the solution.
        """
        cost = 0
        for u, v in self.best_solution:
            cost += self.graph[u][v]['weight']

        return cost 

    def evaluate_path(self, path):
            """Helper to evaluate the cost of a sequence of vertices."""
            cost = 0
            for u, v in zip(path, path[1:]):
                cost += self.graph[u][v]['weight']
            return cost

    def generate_random_path(self):
        """Generates a random valid path to populate the initial generation."""
        start_node = random.choice(list(self.graph.nodes))
        path = [start_node]
        visited = {start_node}
        while True:
            # Encontra vizinhos não visitados
            neighbors = [n for n in self.graph.neighbors(path[-1]) if n not in visited]
            if not neighbors:
                break
            # Escolhe um vizinho aleatoriamente
            next_node = random.choice(neighbors)
            path.append(next_node)
            visited.add(next_node)
        return path

    def crossover(self, p1, p2):
        """
        1-point crossover based on a common vertex.
        Combines the first part of p1 with the second part of p2.
        """
        common_nodes = set(p1) & set(p2)
        if not common_nodes:
            # Se não houver vértices em comum, retorna o melhor dos dois pais
            return p1.copy() if self.evaluate_path(p1) > self.evaluate_path(p2) else p2.copy()
        
        # Escolhe um ponto de cruzamento (vértice comum) aleatório
        c = random.choice(list(common_nodes))
        idx1 = p1.index(c)
        idx2 = p2.index(c)
        
        # Funde as duas partes
        new_path = p1[:idx1] + p2[idx2:]
        
        # Valida o novo caminho para garantir que não há ciclos (vértices repetidos)
        valid_path = []
        visited = set()
        for node in new_path:
            if node in visited:
                break
            if valid_path and not self.graph.has_edge(valid_path[-1], node):
                break
            valid_path.append(node)
            visited.add(node)
            
        return valid_path

    def genetic_algorithm(self):
        """
        Genetic Algorithm (GA) for the Longest Path Problem.
        """
        print("Executing Genetic Algorithm...")
        start_time = time.time()
        max_time = 30  # Critério de paragem: 30 segundos
        pop_size = 50  # Tamanho da população

        population = []
        
        # 1. Inicialização: Um indivíduo construtivo (guloso) e os restantes aleatórios
        self.construtiva()
        greedy_path = self._valid_path_prefix(self.best_solution)
        population.append(greedy_path)
        
        while len(population) < pop_size:
            population.append(self.generate_random_path())
            
        best_global_path = max(population, key=self.evaluate_path)
        best_global_cost = self.evaluate_path(best_global_path)

        # 2. Ciclo das gerações até o tempo limite se esgotar
        while (time.time() - start_time) < max_time:
            new_population = []
            
            # Elitismo: mantém os 2 melhores indivíduos intactos para a próxima geração
            population.sort(key=self.evaluate_path, reverse=True)
            new_population.extend(population[:2])
            
            while len(new_population) < pop_size:
                # Seleção por Torneio (escolhe 3 aleatórios e fica com o melhor)
                p1 = max(random.sample(population, 3), key=self.evaluate_path)
                p2 = max(random.sample(population, 3), key=self.evaluate_path)
                
                # Cruzamento (Crossover) - taxa de 80%
                if random.random() < 0.8:
                    child = self.crossover(p1, p2)
                else:
                    child = p1.copy()
                
                # Mutação - taxa de 20% (utilizamos a perturbação desenvolvida antes)
                if random.random() < 0.2:
                    child = self.perturbation(child)
                    
                new_population.append(child)
                
            population = new_population
            
            # Atualiza a melhor solução global encontrada
            current_best = max(population, key=self.evaluate_path)
            current_cost = self.evaluate_path(current_best)
            if current_cost > best_global_cost:
                best_global_cost = current_cost
                best_global_path = current_best
                
        # Converte de volta para lista de arestas no formato esperado pela classe
        self.best_solution = list(zip(best_global_path, best_global_path[1:]))
        return self.best_solution