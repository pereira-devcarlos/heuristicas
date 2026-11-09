import itertools
import unittest

from heuristics import Heuristics, Individual, dominates, rank_population


class NSGA2Tests(unittest.TestCase):
    def test_dominance_and_ranks(self):
        points = [(9, 3), (5, 8), (4, 2), (9, 3)]
        population = [Individual([], [], p) for p in points]
        fronts = rank_population(population)
        self.assertEqual([len(f) for f in fronts], [3, 1])
        self.assertFalse(dominates((9, 3), (9, 3)))
        self.assertFalse(dominates((9, 3), (5, 8)))
        self.assertTrue(dominates((9, 3), (4, 2)))

    def test_exact_front_on_small_graph(self):
        # Todos os caminhos não triviais deste triângulo são enumeráveis.
        graph = [{1: (9, 1), 2: (5, 5)},
                 {0: (9, 1), 2: (1, 9)},
                 {0: (5, 5), 1: (1, 9)}]
        vectors = set()
        for size in (2, 3):
            for path in itertools.permutations(range(3), size):
                vectors.add(tuple(sum(graph[u][v][j] for u, v in zip(path, path[1:]))
                                  for j in range(2)))
        exact = {a for a in vectors if not any(dominates(b, a) for b in vectors)}
        result = Heuristics(graph, 42).nsga2(60, 30)
        self.assertEqual({x.objectives for x in result}, exact)
        for x in result:
            self.assertEqual(len(x.path), len(set(x.path)))
            self.assertGreaterEqual(len(x.path), 2)
            self.assertEqual(x.objectives, tuple(
                sum(graph[u][v][j] for u, v in zip(x.path, x.path[1:])) for j in range(2)))
        repeat = Heuristics(graph, 42).nsga2(60, 30)
        self.assertEqual([(x.objectives, x.path) for x in result],
                         [(x.objectives, x.path) for x in repeat])

    def test_negative_weights_and_isolated_vertex(self):
        graph = [{}, {2: (-5, -2)}, {1: (-5, -2)}]
        result = Heuristics(graph, 1).nsga2(5, 3)
        self.assertEqual([x.objectives for x in result], [(-5, -2)])
        with self.assertRaises(ValueError):
            Heuristics([{}, {}])

    def test_environmental_selection_preserves_extremes(self):
        individuals = [Individual([], [], p) for p in [(0, 10), (5, 5), (10, 0), (0, 0)]]
        selected = Heuristics.select(individuals, 2)
        self.assertEqual({x.objectives for x in selected}, {(0, 10), (10, 0)})


if __name__ == '__main__':
    unittest.main()
