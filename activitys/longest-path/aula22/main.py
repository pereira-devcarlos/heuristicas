"""Leitura, execução e visualização sem bibliotecas externas."""
import argparse
import csv
import json
import math
from pathlib import Path
import time

from heuristics import Heuristics


def read_instance(path):
    with open(path) as file:
        n, m = map(int, file.readline().split())
        if n < 2 or m < 1:
            raise ValueError('São necessários pelo menos dois vértices e uma aresta.')
        graph = [{} for _ in range(n)]
        count = 0
        for line in file:
            if not line.strip():
                continue
            u, v, w1, w2 = line.split()
            u, v = int(u), int(v)
            weights = float(w1), float(w2)
            if not (0 <= u < n and 0 <= v < n) or u == v:
                raise ValueError('Extremos inválidos ou laço na instância.')
            if v in graph[u] or not all(math.isfinite(w) for w in weights):
                raise ValueError('Aresta duplicada ou peso não finito.')
            graph[u][v] = graph[v][u] = weights
            count += 1
        if count != m:
            raise ValueError(f'Esperadas {m} arestas, encontradas {count}.')
    return graph


def plot_front(front, path):
    """Gráfico de dispersão SVG: os pontos são caminhos, sem interpolação."""
    xs, ys = zip(*(individual.objectives for individual in front))
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    dx, dy = xmax - xmin or 1, ymax - ymin or 1
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">',
        '<rect width="800" height="600" fill="white"/>',
        '<g font-family="sans-serif" font-size="14" fill="#222">',
        '<text x="100" y="30">Fronteira aproximada de Pareto — maximizar W1 e W2</text>',
        '<path d="M90 60V510H740" fill="none" stroke="#222"/>',
        '<text x="370" y="575">W1 (maior é melhor)</text>',
        '<text transform="translate(22 360) rotate(-90)">W2 (maior é melhor)</text>',
    ]
    for i in range(6):
        t = i / 5
        x, y = 110 + t * 600, 490 - t * 400
        elements.append(f'<text x="{x}" y="535" text-anchor="middle">{xmin + t*dx:.1f}</text>')
        elements.append(f'<text x="80" y="{y}" text-anchor="end">{ymin + t*dy:.1f}</text>')
    for individual in front:
        w1, w2 = individual.objectives
        x, y = 110 + 600 * (w1 - xmin) / dx, 490 - 400 * (w2 - ymin) / dy
        elements.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#2563eb"><title>W1={w1}, W2={w2}</title></circle>')
    elements.append('</g></svg>')
    path.write_text('\n'.join(elements), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('instance', type=Path)
    parser.add_argument('--population', type=int, default=100)
    parser.add_argument('--generations', type=int, default=100)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--output', type=Path, default=Path('resultados'))
    args = parser.parse_args()
    try:
        graph = read_instance(args.instance)
        start = time.perf_counter()
        front = Heuristics(graph, args.seed).nsga2(args.population, args.generations)
        elapsed = time.perf_counter() - start
    except (OSError, ValueError) as error:
        parser.error(str(error))
    args.output.mkdir(parents=True, exist_ok=True)
    name = args.output / f'{args.instance.stem}-s{args.seed}'
    with name.with_suffix('.csv').open('w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['w1', 'w2', 'arestas', 'caminho'])
        for individual in front:
            writer.writerow([*individual.objectives, len(individual.path)-1,
                             ' '.join(map(str, individual.path))])
    name.with_suffix('.json').write_text(json.dumps({
        'instance': str(args.instance), 'seed': args.seed,
        'population': args.population, 'generations': args.generations,
        'evaluations': args.population * (args.generations + 1),
        'seconds': elapsed, 'points': len(front),
    }, indent=2), encoding='utf-8')
    plot_front(front, name.with_suffix('.svg'))
    print(f'{len(front)} vetores não dominados na população final; {elapsed:.3f} s.')
    print(f'Resultados: {name}.csv, .json e .svg')


if __name__ == '__main__':
    main()
