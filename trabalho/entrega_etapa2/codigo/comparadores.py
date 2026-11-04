"""Comparadores locais: não representam Kubernetes, Multiopt ou o Greedy do artigo."""

import random
from time import perf_counter

from .modelo import Instancia, avaliar, domina
from .moma import Individuo, inicializar


METODOS = ("aleatorio", "guloso_recursos", "guloso_comunicacao")


def executar_comparador(instancia: Instancia, metodo: str, orcamento: int, semente: int) -> dict:
    if metodo not in METODOS or type(orcamento) is not int or orcamento < 1:
        raise ValueError("Comparador desconhecido ou orçamento inválido.")
    inicio = perf_counter()
    rng = random.Random(semente)
    fronteira = []
    avaliacoes = 0
    avaliacoes_viaveis = 0
    menor_violacao = float("inf")

    def avaliar_candidato(alocacao):
        nonlocal fronteira, avaliacoes, avaliacoes_viaveis, menor_violacao
        av = avaliar(instancia, alocacao)
        avaliacoes += 1
        menor_violacao = min(menor_violacao, av.violacao)
        if av.viavel:
            avaliacoes_viaveis += 1
            if (not any(domina(ind.avaliacao, av) for ind in fronteira)
                    and not any(ind.avaliacao.objetivos == av.objetivos for ind in fronteira)):
                fronteira = [ind for ind in fronteira if not domina(av, ind.avaliacao)]
                fronteira.append(Individuo([linha[:] for linha in alocacao], av))
        return av

    while avaliacoes < orcamento:
        if metodo == "aleatorio":
            avaliar_candidato(inicializar(instancia, rng))
            continue
        # Reinícios com ordens diferentes; usa somente o mínimo exigido de réplicas.
        alocacao = [[0] * len(instancia.nos) for _ in instancia.servicos]
        tarefas = [i for i, s in enumerate(instancia.servicos) for _ in range(s.replicas_min)]
        rng.shuffle(tarefas)
        for i in tarefas:
            candidatos = []
            for h in range(len(instancia.nos)):
                if avaliacoes == orcamento:
                    break
                alocacao[i][h] += 1
                av = avaliar_candidato(alocacao)
                alocacao[i][h] -= 1
                objetivos = av.objetivos if metodo == "guloso_recursos" else av.objetivos[::-1]
                candidatos.append(((av.violacao, *objetivos), h))
            if not candidatos:
                break
            melhor = min(chave for chave, _ in candidatos)
            h = rng.choice([h for chave, h in candidatos if chave == melhor])
            alocacao[i][h] += 1
            if avaliacoes == orcamento:
                break
    fronteira.sort(key=lambda ind: ind.avaliacao.objetivos)
    return {
        "instancia": instancia.nome, "metodo": metodo, "modelo": "moma-operacional-v1",
        "semente": semente, "avaliacoes": avaliacoes,
        "avaliacoes_viaveis": avaliacoes_viaveis, "menor_violacao_avaliada": menor_violacao,
        "tempo_segundos": perf_counter() - inicio,
        "pontos_nao_dominados": [list(ind.avaliacao.objetivos) for ind in fronteira],
        "fronteira": [{"alocacao": ind.alocacao, "objetivos": list(ind.avaliacao.objetivos),
                       "violacao": ind.avaliacao.violacao,
                       "sigma_cluster": ind.avaliacao.sigma_cluster} for ind in fronteira],
    }
