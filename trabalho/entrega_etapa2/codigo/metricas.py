"""Hipervolume bidimensional para objetivos de minimização."""

import math

from .modelo import Instancia


def escala_comunicacao(instancia: Instancia) -> float:
    """Limite conservador independente das soluções produzidas por cada método."""
    volume = sum(i.volume for i in instancia.interacoes)
    distancia = max(max(linha) for linha in instancia.distancias)
    falha = max(no.falha for no in instancia.nos)
    return max(1.0, volume * distancia * (1 + falha))


def hipervolume(pontos: list, referencia: tuple[float, float] = (1.1, 1.1)) -> float:
    if len(referencia) != 2 or not all(math.isfinite(v) for v in referencia):
        raise ValueError("Referência deve ter duas coordenadas finitas.")
    for ponto in pontos:
        if len(ponto) != 2 or not all(math.isfinite(v) for v in ponto):
            raise ValueError("Cada ponto deve ter duas coordenadas finitas.")
        if any(v >= r for v, r in zip(ponto, referencia)):
            raise ValueError("O ponto de referência deve ser estritamente maior que os pontos.")
    area = 0.0
    altura = referencia[1]
    for x, y in sorted({tuple(ponto) for ponto in pontos}):
        if y < altura:
            area += (referencia[0] - x) * (altura - y)
            altura = y
    return area


def medir(instancia: Instancia, pontos: list) -> dict:
    escala = escala_comunicacao(instancia)
    normalizados = [[x, y / escala] for x, y in pontos]
    return {"escala_comunicacao": escala, "referencia_normalizada": [1.1, 1.1],
            "hipervolume": hipervolume(normalizados),
            "pontos": len(pontos),
            "menor_balanceamento": min((x for x, _ in pontos), default=None),
            "menor_comunicacao": min((y for _, y in pontos), default=None)}
