"""Compara execuções do MOMA à fronteira exata de uma instância pequena."""

import math
import platform
from dataclasses import asdict, replace

from .exato import enumerar
from .modelo import Instancia
from .moma import Parametros, executar


def mesmos_pontos(a: list, b: list) -> bool:
    def coberto(ponto, conjunto):
        return any(all(math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9)
                       for x, y in zip(ponto, outro)) for outro in conjunto)

    return all(coberto(p, b) for p in a) and all(coberto(p, a) for p in b)


def validar(instancia: Instancia, parametros: Parametros, sementes: list[int],
            limite: int = 100_000) -> dict:
    if not sementes or len(set(sementes)) != len(sementes):
        raise ValueError("Informe sementes distintas e pelo menos uma execução.")
    referencia = enumerar(instancia, limite)
    if not referencia["pontos_nao_dominados"]:
        raise ValueError("A instância não possui solução viável para validar a busca.")
    execucoes = []
    for semente in sementes:
        resultado = executar(instancia, replace(parametros, semente=semente))
        pontos = resultado["pontos_nao_dominados"]
        execucoes.append({
            "semente": semente,
            "avaliacoes": resultado["avaliacoes"],
            "tempo_segundos": resultado["tempo_segundos"],
            "fronteira_exata_recuperada": mesmos_pontos(
                pontos, referencia["pontos_nao_dominados"]),
            "pontos_nao_dominados": pontos,
        })
    parametros_comuns = asdict(parametros)
    parametros_comuns.pop("semente")
    return {
        "instancia": instancia.nome,
        "modelo": "moma-operacional-v1",
        "python": platform.python_version(),
        "tolerancia_relativa": 1e-9,
        "tolerancia_absoluta": 1e-9,
        "parametros_comuns": parametros_comuns,
        "referencia_exata": referencia,
        "total_execucoes": len(execucoes),
        "execucoes_com_fronteira_exata": sum(e["fronteira_exata_recuperada"] for e in execucoes),
        "execucoes": execucoes,
    }
