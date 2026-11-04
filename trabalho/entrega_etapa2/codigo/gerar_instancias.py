"""Gera instâncias híbridas: recursos publicados e rede/infraestrutura sintéticas."""

import json
import random
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
SEMENTES = {"edgex": 101, "sockshop": 102, "kubeflow": 103}


def gerar(destino: Path = RAIZ / "dados" / "experimentos") -> list[Path]:
    dados = json.loads((RAIZ / "dados" / "recursos_artigo.json").read_text(encoding="utf-8"))
    destino.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for chave, aplicacao in dados["aplicacoes"].items():
        rng = random.Random(SEMENTES[chave])
        demandas = aplicacao["10"]
        total_cpu = sum(cpu for cpu, _ in demandas)
        total_mem = sum(mem for _, mem in demandas)
        maior_cpu = max(cpu for cpu, _ in demandas)
        maior_mem = max(mem for _, mem in demandas)
        nos = []
        for h, fracao in enumerate((1.05, 0.25, 0.60, 0.20, 0.70, 0.35)):
            # Nós pares também comportam o maior serviço individual.
            cpu = max(total_cpu * fracao, maior_cpu * 1.05 if h % 2 == 0 else 0)
            memoria = max(total_mem * fracao, maior_mem * 1.05 if h % 2 == 0 else 0)
            nos.append({"id": f"n{h}", "cluster": f"c{h // 2}",
                        "cpu": round(cpu, 6), "memoria": round(memoria, 6),
                        "falha": round(rng.uniform(0.01, 0.03), 6)})
        distancias = [[0.0] * 6 for _ in range(6)]
        for h in range(6):
            for k in range(h + 1, 6):
                intervalo = (1.0, 1.5) if h // 2 == k // 2 else (2.5, 4.0)
                valor = round(rng.uniform(*intervalo), 6)
                distancias[h][k] = distancias[k][h] = valor
        interacoes = []
        ids = aplicacao["ids"]
        for i, origem in enumerate(ids):
            for j, destino_servico in enumerate(ids):
                if i == j:
                    continue
                probabilidade = 0.65 if i // 3 == j // 3 else 0.10
                sorteio = rng.random()
                if j == (i + 1) % len(ids) or sorteio < probabilidade:
                    interacoes.append({"origem": origem, "destino": destino_servico,
                                       "volume": round(rng.uniform(1, 10), 6)})
        for usuarios in (1, 10):
            recursos = aplicacao[str(usuarios)]
            if len(recursos) != len(ids):
                raise ValueError("Quantidade de demandas e IDs diferente.")
            instancia = {
                "modelo": "moma-operacional-v1",
                "nome": f"{chave}_{usuarios}_usuarios_hibrida",
                "origem": {
                    "tipo": "hibrida",
                    "aplicacao": aplicacao["nome"], "usuarios": usuarios,
                    "recursos": {"arquivo": "../recursos_artigo.json",
                                 "doi": dados["origem"]["doi"],
                                 **dados["origem"]["tabelas"][str(usuarios)]},
                    "infraestrutura": "sintetica; regra em gerar_instancias.py, dimensionada pela carga de dez usuarios",
                    "rede": "sintetica; nao utiliza a coluna Interaction do artigo",
                    "trafego": "grafo dirigido sintetico com volumes base uniformes [1,10] multiplicados pelo numero de usuarios",
                    "replicas": "limites sinteticos: uma a duas por servico; custo fixo por replica",
                    "semente_geracao": SEMENTES[chave],
                    "unidade_cpu": "cores", "unidade_memoria": "Mbytes",
                    "unidade_volume": "unidades arbitrarias de dados por segundo"
                },
                "nos": nos, "distancias": distancias,
                "servicos": [{"id": id_servico, "cpu": cpu, "memoria": memoria,
                              "replicas_min": 1, "replicas_max": 2}
                             for id_servico, (cpu, memoria) in zip(ids, recursos)],
                "interacoes": [{**item, "volume": round(item["volume"] * usuarios, 6)}
                               for item in interacoes],
            }
            caminho = destino / f"{chave}_{usuarios}.json"
            caminho.write_text(json.dumps(instancia, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
            caminhos.append(caminho)
    return caminhos


if __name__ == "__main__":
    for caminho in gerar():
        print(caminho)
