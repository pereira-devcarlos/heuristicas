"""Enumeração exata para instâncias pequenas, independente da busca evolutiva."""

import math
from itertools import product

from .modelo import Instancia, avaliar, domina


def distribuicoes(total: int, quantidade_nos: int):
    """Composições fracas: permite réplicas do mesmo serviço no mesmo nó."""
    if quantidade_nos == 1:
        yield [total]
        return
    for quantidade in range(total + 1):
        for restante in distribuicoes(total - quantidade, quantidade_nos - 1):
            yield [quantidade, *restante]


def enumerar(instancia: Instancia, limite: int = 100_000) -> dict:
    n = len(instancia.nos)
    tamanhos = [sum(math.comb(r + n - 1, n - 1)
                    for r in range(s.replicas_min, s.replicas_max + 1))
                for s in instancia.servicos]
    total = math.prod(tamanhos)
    if total > limite:
        raise ValueError(f"Enumeração teria {total} soluções; limite: {limite}.")
    opcoes = [[linha for r in range(s.replicas_min, s.replicas_max + 1)
               for linha in distribuicoes(r, n)] for s in instancia.servicos]
    fronteira = []
    viaveis = 0
    for linhas in product(*opcoes):
        alocacao = [linha[:] for linha in linhas]
        avaliacao = avaliar(instancia, alocacao)
        if not avaliacao.viavel:
            continue
        viaveis += 1
        if any(domina(av, avaliacao) for _, av in fronteira):
            continue
        fronteira = [(x, av) for x, av in fronteira if not domina(avaliacao, av)]
        fronteira.append((alocacao, avaliacao))
    fronteira.sort(key=lambda item: item[1].objetivos)
    pontos = sorted({av.objetivos for _, av in fronteira})
    return {
        "instancia": instancia.nome,
        "metodo": "enumeracao_exata",
        "modelo": "moma-operacional-v1",
        "solucoes_enumeradas": total,
        "solucoes_viaveis": viaveis,
        "pontos_nao_dominados": [list(ponto) for ponto in pontos],
        "fronteira": [{"alocacao": x, "objetivos": list(av.objetivos),
                       "violacao": av.violacao} for x, av in fronteira],
    }
