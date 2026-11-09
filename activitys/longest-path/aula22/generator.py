"""Gera instâncias conexas biobjetivo ou converte uma instância mono-objetivo."""
import argparse
from pathlib import Path
import random


def generate(n, probability, rng):
    # Uma árvore inicial garante conexão, sem repetir tentativas indefinidamente.
    edges = {(rng.randrange(v), v) for v in range(1, n)}
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < probability:
                edges.add((u, v))
    return [(u, v, rng.randint(1, 100)) for u, v in sorted(edges)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nodes', type=int, default=30)
    parser.add_argument('--probability', type=float, default=0.15)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--mode', choices=['independent', 'conflicting'], default='independent')
    parser.add_argument('--source', type=Path, help='Instância mono-objetivo a converter')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.nodes < 2 or not 0 <= args.probability <= 1:
        parser.error('Use nodes >= 2 e probability entre 0 e 1.')
    rng = random.Random(args.seed)
    if args.source:
        with args.source.open() as file:
            n, m = map(int, file.readline().split())
            edges = []
            for line in file:
                if line.strip():
                    u, v, weight = line.split()
                    edges.append((int(u), int(v), float(weight)))
        if len(edges) != m or not edges:
            parser.error('Número de arestas inconsistente ou instância sem arestas.')
    else:
        n = args.nodes
        edges = generate(n, args.probability, rng)
    # Na modalidade conflitante, pesos altos em W1 recebem pesos baixos em W2.
    # Isso favorece compromissos por aresta, sem garantir conflito entre caminhos.
    ceiling = max(edge[2] for edge in edges) + min(edge[2] for edge in edges)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w') as file:
        file.write(f'{n} {len(edges)}\n')
        for u, v, w1 in edges:
            w2 = rng.randint(1, 100) if args.mode == 'independent' else ceiling - w1
            file.write(f'{u} {v} {w1:g} {w2:g}\n')
    print(f'Instância salva em {args.output}')


if __name__ == '__main__':
    main()
