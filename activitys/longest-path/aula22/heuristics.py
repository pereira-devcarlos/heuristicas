"""NSGA-II com representação indireta por chaves aleatórias (maximização)."""

from dataclasses import dataclass
import random


@dataclass
class Individual:
    keys: list[float]
    path: list[int]
    objectives: tuple[float, float]
    rank: int = 0
    crowding: float = 0.0


def dominates(a, b):
    return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))


def rank_population(population):
    """Ordenação não dominada O(M N²), seguida da distância em cada frente."""
    dominated = [[] for _ in population]
    counts = [0] * len(population)
    fronts = [[]]
    for i, a in enumerate(population):
        for j in range(i + 1, len(population)):
            b = population[j]
            if dominates(a.objectives, b.objectives):
                dominated[i].append(j)
                counts[j] += 1
            elif dominates(b.objectives, a.objectives):
                dominated[j].append(i)
                counts[i] += 1
    fronts[0] = [i for i, count in enumerate(counts) if count == 0]
    result = []
    level = 0
    while fronts[level]:
        front = [population[i] for i in fronts[level]]
        for individual in front:
            individual.rank = level
        crowding_distance(front)
        result.append(front)
        following = []
        for i in fronts[level]:
            for j in dominated[i]:
                counts[j] -= 1
                if counts[j] == 0:
                    following.append(j)
        fronts.append(following)
        level += 1
    return result


def crowding_distance(front):
    for individual in front:
        individual.crowding = 0.0
    if len(front) <= 2:
        for individual in front:
            individual.crowding = float('inf')
        return
    for objective in range(2):
        ordered = sorted(front, key=lambda x: x.objectives[objective])
        low = ordered[0].objectives[objective]
        high = ordered[-1].objectives[objective]
        if high == low:
            continue
        ordered[0].crowding = ordered[-1].crowding = float('inf')
        for i in range(1, len(ordered) - 1):
            ordered[i].crowding += (
                ordered[i + 1].objectives[objective]
                - ordered[i - 1].objectives[objective]
            ) / (high - low)


class Heuristics:
    def __init__(self, graph, seed=0):
        self.graph = graph
        self.rng = random.Random(seed)
        self.starts = [u for u, neighbors in enumerate(graph) if neighbors]
        if not self.starts:
            raise ValueError('O grafo precisa ter ao menos uma aresta.')

    def decode(self, keys):
        """n prioridades, uma chave de início e uma de comprimento.

        O comprimento variável também permite caminhos curtos, essenciais quando
        existem pesos negativos. A primeira aresta é sempre obrigatória.
        """
        n = len(self.graph)
        current = self.starts[int(keys[n] * len(self.starts))]
        limit = 1 + int(keys[n + 1] * (n - 1))
        path = [current]
        visited = {current}
        weights = [0.0, 0.0]
        while len(path) - 1 < limit:
            candidates = [v for v in self.graph[current] if v not in visited]
            if not candidates:
                break
            following = min(candidates, key=lambda v: (keys[v], v))
            w1, w2 = self.graph[current][following]
            weights[0] += w1
            weights[1] += w2
            path.append(following)
            visited.add(following)
            current = following
        return Individual(keys, path, tuple(weights))

    def tournament(self, population):
        a, b = self.rng.sample(population, 2)
        ka, kb = (a.rank, -a.crowding), (b.rank, -b.crowding)
        if ka == kb:
            return self.rng.choice([a, b])
        return a if ka < kb else b

    def nsga2(self, population_size=100, generations=100, mutation_rate=None):
        if population_size < 2 or generations < 0:
            raise ValueError('População deve ser >= 2 e gerações >= 0.')
        dimension = len(self.graph) + 2
        rate = 1 / dimension if mutation_rate is None else mutation_rate
        if not 0 <= rate <= 1:
            raise ValueError('Taxa de mutação deve estar entre 0 e 1.')
        population = [self.decode([self.rng.random() for _ in range(dimension)])
                      for _ in range(population_size)]
        rank_population(population)
        for _ in range(generations):
            offspring = []
            for _ in range(population_size):
                a, b = self.tournament(population), self.tournament(population)
                # Cruzamento uniforme; mutação sorteia novamente cada gene afetado.
                keys = [self.rng.choice((x, y)) for x, y in zip(a.keys, b.keys)]
                for j in range(dimension):
                    if self.rng.random() < rate:
                        keys[j] = self.rng.random()
                offspring.append(self.decode(keys))
            # Seleção elitista de N indivíduos dentre os 2N pais e filhos.
            population = self.select(population + offspring, population_size)
        # Retorna um representante por vetor objetivo da primeira frente.
        front = rank_population(population)[0]
        unique = {individual.objectives: individual for individual in front}
        return sorted(unique.values(), key=lambda x: x.objectives)

    @staticmethod
    def select(combined, size):
        selected = []
        for front in rank_population(combined):
            remaining = size - len(selected)
            selected.extend(sorted(front, key=lambda x: x.crowding, reverse=True)[:remaining])
            if len(selected) == size:
                break
        return selected
