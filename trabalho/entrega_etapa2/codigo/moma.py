"""Busca MOMA com NSGA-II e adaptações inteiras descritas na documentação."""

import math
import random
from dataclasses import asdict, dataclass
from time import perf_counter

from .modelo import Avaliacao, Instancia, avaliar, domina


@dataclass(frozen=True)
class Parametros:
    populacao: int = 200
    descendentes: int = 200
    geracoes: int = 100
    prob_cruzamento: float = 0.5
    prob_mutacao: float = 0.3
    eta: float = 10.0
    semente: int = 0

    def __post_init__(self):
        for nome, minimo in (("populacao", 2), ("descendentes", 1), ("geracoes", 0)):
            valor = getattr(self, nome)
            if type(valor) is not int or valor < minimo:
                raise ValueError(f"{nome} deve ser inteiro >= {minimo}.")
        if type(self.semente) is not int:
            raise ValueError("A semente deve ser inteira.")
        for nome in ("prob_cruzamento", "prob_mutacao", "eta"):
            valor = getattr(self, nome)
            if (isinstance(valor, bool) or not isinstance(valor, (int, float))
                    or not math.isfinite(valor) or valor < 0):
                raise ValueError(f"{nome} deve ser um número finito não negativo.")
        if self.prob_cruzamento > 1 or self.prob_mutacao > 1:
            raise ValueError("Probabilidades devem estar em [0, 1].")


@dataclass
class Individuo:
    alocacao: list[list[int]]
    avaliacao: Avaliacao
    rank: int = 0
    distancia: float = 0.0


def ordenar_frentes(populacao: list[Individuo]) -> list[list[Individuo]]:
    """Ordenação não dominada O(N²), considerando viabilidade primeiro."""
    dominados = [[] for _ in populacao]
    contagens = [0] * len(populacao)
    for i in range(len(populacao)):
        for j in range(i + 1, len(populacao)):
            if domina(populacao[i].avaliacao, populacao[j].avaliacao):
                dominados[i].append(j)
                contagens[j] += 1
            elif domina(populacao[j].avaliacao, populacao[i].avaliacao):
                dominados[j].append(i)
                contagens[i] += 1
    atual = [i for i, contagem in enumerate(contagens) if contagem == 0]
    frentes = []
    while atual:
        frente = []
        proxima = []
        for i in atual:
            individuo = populacao[i]
            individuo.rank = len(frentes)
            frente.append(individuo)
            for j in dominados[i]:
                contagens[j] -= 1
                if contagens[j] == 0:
                    proxima.append(j)
        frentes.append(frente)
        atual = proxima
    return frentes


def calcular_distancias(frente: list[Individuo]) -> None:
    """Crowding distance normalizada por objetivo; objetivos constantes não contam."""
    for individuo in frente:
        individuo.distancia = 0.0
    if len(frente) <= 2:
        for individuo in frente:
            individuo.distancia = math.inf
        return
    for objetivo in range(2):
        ordenados = sorted(frente, key=lambda ind: ind.avaliacao.objetivos[objetivo])
        minimo = ordenados[0].avaliacao.objetivos[objetivo]
        maximo = ordenados[-1].avaliacao.objetivos[objetivo]
        amplitude = maximo - minimo
        if amplitude == 0:
            continue
        ordenados[0].distancia = ordenados[-1].distancia = math.inf
        for i in range(1, len(ordenados) - 1):
            anterior = ordenados[i - 1].avaliacao.objetivos[objetivo]
            seguinte = ordenados[i + 1].avaliacao.objetivos[objetivo]
            ordenados[i].distancia += (seguinte - anterior) / amplitude


def selecionar_ambiente(populacao: list[Individuo], tamanho: int,
                       rng: random.Random) -> list[Individuo]:
    selecionados = []
    for frente in ordenar_frentes(populacao):
        calcular_distancias(frente)
        vagas = tamanho - len(selecionados)
        if len(frente) <= vagas:
            selecionados.extend(frente)
        else:
            # Empates de distância não favorecem sempre os primeiros pais.
            candidatos = frente[:]
            rng.shuffle(candidatos)
            candidatos.sort(key=lambda ind: ind.distancia, reverse=True)
            selecionados.extend(candidatos[:vagas])
        if len(selecionados) == tamanho:
            break
    return selecionados


def torneio(populacao: list[Individuo], rng: random.Random) -> Individuo:
    a, b = rng.sample(populacao, 2)
    chave_a = (a.rank, -a.distancia)
    chave_b = (b.rank, -b.distancia)
    if chave_a == chave_b:
        return rng.choice((a, b))
    return a if chave_a < chave_b else b


def inicializar(instancia: Instancia, rng: random.Random) -> list[list[int]]:
    alocacao = []
    for servico in instancia.servicos:
        linha = [0] * len(instancia.nos)
        total = rng.randint(servico.replicas_min, servico.replicas_max)
        for _ in range(total):
            linha[rng.randrange(len(linha))] += 1
        alocacao.append(linha)
    return alocacao


def reparar_replicas(instancia: Instancia, alocacao: list[list[int]],
                     rng: random.Random) -> None:
    """Repara apenas totais por serviço; capacidade física usa dominância por restrições."""
    for linha, servico in zip(alocacao, instancia.servicos):
        total = sum(linha)
        while total > servico.replicas_max:
            h = rng.choice([h for h, quantidade in enumerate(linha) if quantidade > 0])
            linha[h] -= 1
            total -= 1
        while total < servico.replicas_min:
            linha[rng.randrange(len(linha))] += 1
            total += 1


def cruzar(instancia: Instancia, pai: list[list[int]], mae: list[list[int]],
           parametros: Parametros, rng: random.Random) -> tuple[list[list[int]], list[list[int]]]:
    filho = [linha[:] for linha in pai]
    filha = [linha[:] for linha in mae]
    if rng.random() >= parametros.prob_cruzamento:
        return filho, filha
    for i, servico in enumerate(instancia.servicos):
        for h in range(len(instancia.nos)):
            p, q = pai[i][h], mae[i][h]
            u = rng.random()
            expoente = 1 / (parametros.eta + 1)
            beta = ((2 * u)**expoente if u <= 0.5
                    else (1 / (2 * (1 - u)))**expoente)
            valores = (0.5 * ((p + q) - beta * (q - p)),
                       0.5 * ((p + q) + beta * (q - p)))
            for matriz, valor in zip((filho, filha), valores):
                # Limite antes do arredondamento evita valores enormes fora do domínio.
                limitado = min(servico.replicas_max, max(0.0, valor))
                matriz[i][h] = math.floor(limitado + 0.5)
    reparar_replicas(instancia, filho, rng)
    reparar_replicas(instancia, filha, rng)
    return filho, filha


def mutar(instancia: Instancia, alocacao: list[list[int]], rng: random.Random) -> None:
    """Sorteia inserção/remoção (50% cada); não troca de operação se ela for impossível."""
    inserir = rng.random() < 0.5
    elegiveis = [i for i, s in enumerate(instancia.servicos)
                 if (sum(alocacao[i]) < s.replicas_max if inserir
                     else sum(alocacao[i]) > s.replicas_min)]
    if not elegiveis:
        return
    i = rng.choice(elegiveis)
    if inserir:
        h = rng.randrange(len(instancia.nos))
        alocacao[i][h] += 1
    else:
        h = rng.choice([h for h, quantidade in enumerate(alocacao[i]) if quantidade > 0])
        alocacao[i][h] -= 1


def executar(instancia: Instancia, parametros: Parametros) -> dict:
    inicio = perf_counter()
    rng = random.Random(parametros.semente)
    avaliacoes = 0

    def criar(alocacao):
        nonlocal avaliacoes
        avaliacoes += 1
        return Individuo(alocacao, avaliar(instancia, alocacao))

    populacao = [criar(inicializar(instancia, rng)) for _ in range(parametros.populacao)]
    populacao = selecionar_ambiente(populacao, parametros.populacao, rng)
    historico = []

    def registrar(geracao):
        viaveis = [ind for ind in populacao if ind.avaliacao.viavel]
        historico.append({
            "geracao": geracao,
            "avaliacoes": avaliacoes,
            "individuos_viaveis": len(viaveis),
            "menor_violacao": min(ind.avaliacao.violacao for ind in populacao),
            "pontos_nao_dominados": len({ind.avaliacao.objetivos for ind in viaveis
                                        if ind.rank == 0}),
        })

    registrar(0)
    for geracao in range(1, parametros.geracoes + 1):
        descendentes = []
        while len(descendentes) < parametros.descendentes:
            pai = torneio(populacao, rng)
            mae = torneio(populacao, rng)
            filhos = cruzar(instancia, pai.alocacao, mae.alocacao, parametros, rng)
            # O sorteio conjunto para o par segue o pseudocódigo do artigo.
            if rng.random() < parametros.prob_mutacao:
                for alocacao in filhos:
                    mutar(instancia, alocacao, rng)
            for alocacao in filhos:
                if len(descendentes) == parametros.descendentes:
                    break
                descendentes.append(criar(alocacao))
        populacao = selecionar_ambiente(populacao + descendentes, parametros.populacao, rng)
        registrar(geracao)

    # Resultado apenas da população final, sem arquivo externo e sem enumeração.
    unicos = {}
    for individuo in populacao:
        if individuo.rank == 0 and individuo.avaliacao.viavel:
            chave = tuple(tuple(linha) for linha in individuo.alocacao)
            unicos[chave] = individuo
    fronteira = sorted(unicos.values(), key=lambda ind: (ind.avaliacao.objetivos, ind.alocacao))
    pontos = sorted({ind.avaliacao.objetivos for ind in fronteira})
    return {
        "instancia": instancia.nome,
        "metodo": "moma_nsga2_adaptado",
        "modelo": "moma-operacional-v1",
        "parametros": asdict(parametros),
        "avaliacoes": avaliacoes,
        "tempo_segundos": perf_counter() - inicio,
        "individuos_finais": len(populacao),
        "individuos_viaveis_finais": sum(ind.avaliacao.viavel for ind in populacao),
        "menor_violacao_final": min(ind.avaliacao.violacao for ind in populacao),
        "pontos_nao_dominados": [list(ponto) for ponto in pontos],
        "fronteira": [{"alocacao": ind.alocacao, "objetivos": list(ind.avaliacao.objetivos),
                       "violacao": ind.avaliacao.violacao,
                       "sigma_cluster": ind.avaliacao.sigma_cluster} for ind in fronteira],
        "historico": historico,
    }
