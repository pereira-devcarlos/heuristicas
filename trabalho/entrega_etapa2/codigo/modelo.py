"""Leitura e avaliação do modelo operacional documentado em modelo_operacional.md."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import pstdev


@dataclass(frozen=True)
class No:
    id: str
    cluster: str
    cpu: float
    memoria: float
    falha: float


@dataclass(frozen=True)
class Servico:
    id: str
    cpu: float
    memoria: float
    replicas_min: int
    replicas_max: int


@dataclass(frozen=True)
class Interacao:
    origem: int
    destino: int
    volume: float


@dataclass(frozen=True)
class Instancia:
    nome: str
    nos: tuple[No, ...]
    servicos: tuple[Servico, ...]
    distancias: tuple[tuple[float, ...], ...]
    interacoes: tuple[Interacao, ...]


@dataclass(frozen=True)
class Avaliacao:
    balanceamento: float
    comunicacao: float
    violacao: float
    cpu_usada: tuple[float, ...]
    memoria_usada: tuple[float, ...]
    sigma_cpu: float
    sigma_memoria: float
    sigma_cluster: float

    @property
    def viavel(self) -> bool:
        return self.violacao == 0.0

    @property
    def objetivos(self) -> tuple[float, float]:
        return self.balanceamento, self.comunicacao


def _numero(valor: object, campo: str, minimo: float = 0.0) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError(f"{campo}: esperado um número.")
    if not math.isfinite(valor) or valor < minimo:
        raise ValueError(f"{campo}: esperado número finito >= {minimo}.")
    return float(valor)


def _inteiro(valor: object, campo: str, minimo: int) -> int:
    if type(valor) is not int or valor < minimo:
        raise ValueError(f"{campo}: esperado inteiro >= {minimo}.")
    return valor


def _texto(valor: object, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{campo}: esperado texto não vazio.")
    return valor


def _lista(valor: object, campo: str, permitir_vazia: bool = False) -> list:
    if not isinstance(valor, list) or (not valor and not permitir_vazia):
        raise ValueError(f"{campo}: esperada lista{' não vazia' if not permitir_vazia else ''}.")
    return valor


def carregar_instancia(caminho: str | Path) -> Instancia:
    """Carrega uma instância completa; rejeita também números NaN e infinitos."""
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    try:
        if dados["modelo"] != "moma-operacional-v1":
            raise ValueError("Versão do modelo desconhecida.")
        nome = _texto(dados["nome"], "nome")
        nos = []
        for item in _lista(dados["nos"], "nos"):
            cpu = _numero(item["cpu"], "cpu do nó")
            memoria = _numero(item["memoria"], "memória do nó")
            falha = _numero(item["falha"], "falha")
            if cpu == 0 or memoria == 0 or falha > 1:
                raise ValueError("Capacidades devem ser positivas e falha deve estar em [0, 1].")
            nos.append(No(_texto(item["id"], "id do nó"),
                          _texto(item["cluster"], "cluster"), cpu, memoria, falha))
        servicos = []
        for item in _lista(dados["servicos"], "servicos"):
            minimo = _inteiro(item["replicas_min"], "replicas_min", 1)
            maximo = _inteiro(item["replicas_max"], "replicas_max", minimo)
            servicos.append(Servico(_texto(item["id"], "id do serviço"),
                                    _numero(item["cpu"], "cpu do serviço"),
                                    _numero(item["memoria"], "memória do serviço"),
                                    minimo, maximo))
        if len({no.id for no in nos}) != len(nos):
            raise ValueError("IDs de nós duplicados.")
        if len({servico.id for servico in servicos}) != len(servicos):
            raise ValueError("IDs de serviços duplicados.")
        matriz = _lista(dados["distancias"], "distancias")
        if len(matriz) != len(nos):
            raise ValueError("A matriz de distâncias deve ter uma linha por nó.")
        distancias = []
        for h, linha in enumerate(matriz):
            if len(_lista(linha, "linha de distâncias")) != len(nos):
                raise ValueError("A matriz de distâncias deve ser quadrada.")
            valores = tuple(_numero(v, "distância") for v in linha)
            if valores[h] != 0:
                raise ValueError("A diagonal da matriz de distâncias deve ser zero.")
            distancias.append(valores)
        indices = {s.id: i for i, s in enumerate(servicos)}
        interacoes = []
        pares = set()
        for item in _lista(dados["interacoes"], "interacoes", permitir_vazia=True):
            origem = indices[item["origem"]]
            destino = indices[item["destino"]]
            if (origem, destino) in pares:
                raise ValueError("Interação duplicada; agregue os volumes antes de carregar.")
            pares.add((origem, destino))
            interacoes.append(Interacao(origem, destino, _numero(item["volume"], "volume")))
    except (KeyError, TypeError) as erro:
        raise ValueError(f"Instância incompleta ou campo inválido: {erro}") from erro
    return Instancia(nome, tuple(nos), tuple(servicos), tuple(distancias), tuple(interacoes))


def avaliar(instancia: Instancia, alocacao: list[list[int]]) -> Avaliacao:
    """Avalia contagens de réplicas; inviabilidade física gera violação, não exceção."""
    if len(alocacao) != len(instancia.servicos):
        raise ValueError("A alocação deve ter uma linha por serviço.")
    for linha in alocacao:
        if len(linha) != len(instancia.nos):
            raise ValueError("A alocação deve ter uma coluna por nó.")
        for quantidade in linha:
            _inteiro(quantidade, "quantidade de réplicas", 0)

    totais = [sum(linha) for linha in alocacao]
    cpu = tuple(sum(alocacao[i][h] * s.cpu for i, s in enumerate(instancia.servicos))
                for h in range(len(instancia.nos)))
    memoria = tuple(sum(alocacao[i][h] * s.memoria for i, s in enumerate(instancia.servicos))
                    for h in range(len(instancia.nos)))
    uso_cpu = [c / no.cpu for c, no in zip(cpu, instancia.nos)]
    uso_mem = [m / no.memoria for m, no in zip(memoria, instancia.nos)]
    violacao = sum(max(0.0, u - 1.0) for u in uso_cpu + uso_mem)
    for total, servico in zip(totais, instancia.servicos):
        violacao += max(0, servico.replicas_min - total) / servico.replicas_min
        violacao += max(0, total - servico.replicas_max) / servico.replicas_max

    grupos: dict[str, list[int]] = {}
    for h, no in enumerate(instancia.nos):
        grupos.setdefault(no.cluster, []).append(h)
    cargas_ponderadas = []
    for indices in grupos.values():
        sigma_cpu = pstdev(uso_cpu[h] for h in indices)
        sigma_mem = pstdev(uso_mem[h] for h in indices)
        soma = sigma_cpu + sigma_mem
        peso_cpu = sigma_cpu / soma if soma > 0 else 0.5
        peso_mem = sigma_mem / soma if soma > 0 else 0.5
        cargas_ponderadas.extend(peso_cpu * uso_cpu[h] + peso_mem * uso_mem[h]
                                for h in indices)

    comunicacao = 0.0
    for interacao in instancia.interacoes:
        origem, destino = interacao.origem, interacao.destino
        if totais[origem] == 0 or totais[destino] == 0:
            # Ausência de serviço é penalizada na violação, acima.
            continue
        for h, no in enumerate(instancia.nos):
            for k in range(len(instancia.nos)):
                if h != k:
                    fracao = (alocacao[origem][h] / totais[origem]
                              * alocacao[destino][k] / totais[destino])
                    comunicacao += (interacao.volume * fracao * (1 + no.falha)
                                    * instancia.distancias[h][k])
    sigma_cpu = pstdev(uso_cpu)
    sigma_mem = pstdev(uso_mem)
    return Avaliacao(max(cargas_ponderadas), comunicacao, violacao, cpu, memoria,
                     sigma_cpu, sigma_mem, 0.5 * math.hypot(sigma_cpu, sigma_mem))


def domina(a: Avaliacao, b: Avaliacao) -> bool:
    """Dominância por restrições e, entre viáveis, dominância de Pareto estrita."""
    if a.viavel != b.viavel:
        return a.viavel
    if not a.viavel:
        return a.violacao < b.violacao
    return (all(x <= y for x, y in zip(a.objetivos, b.objetivos))
            and any(x < y for x, y in zip(a.objetivos, b.objetivos)))
