"""Experimentos locais reproduzíveis com orçamento igual de avaliações."""

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
from dataclasses import asdict, replace
from pathlib import Path

from .comparadores import METODOS, executar_comparador
from .metricas import medir
from .modelo import avaliar, carregar_instancia
from .moma import Parametros, executar


RAIZ = Path(__file__).resolve().parent.parent


def salvar_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                       encoding="utf-8")


def resumir(linhas: list[dict], destino: Path) -> None:
    with (destino / "execucoes.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    resumo = []
    for instancia in sorted({linha["instancia"] for linha in linhas}):
        for metodo in ("moma", *METODOS):
            grupo = [l for l in linhas if l["instancia"] == instancia and l["metodo"] == metodo]
            valores = [l["hipervolume"] for l in grupo]
            resumo.append({
                "instancia": instancia, "metodo": metodo, "execucoes": len(grupo),
                "com_solucao_viavel": sum(l["pontos"] > 0 for l in grupo),
                "hv_media": statistics.mean(valores),
                "hv_desvio_amostral": statistics.stdev(valores) if len(valores) > 1 else 0.0,
                "hv_mediana": statistics.median(valores),
                "tempo_medio_segundos": statistics.mean(l["tempo_segundos"] for l in grupo),
                "pontos_medios": statistics.mean(l["pontos"] for l in grupo),
            })
    salvar_json(destino / "resumo.json", {"grupos": resumo})
    texto = [
        "# Resultados dos experimentos locais", "",
        "Instâncias híbridas: CPU e memória das Tabelas 4 e 5 de Chen e Wen (2024); "
        "infraestrutura, rede, tráfego e limites de réplicas sintéticos. "
        "Os comparadores são implementações locais, não os algoritmos originais do artigo.", "",
        "O hipervolume (HV) usa minimização e referência normalizada (1,1; 1,1). "
        "CPU/memória geram objetivo de recursos no intervalo [0; 1] para soluções viáveis; "
        "comunicação é dividida por um limite conservador obtido da instância. "
        "HV maior indica melhor cobertura no modelo local. Não é percentual de utilização.", "",
        "| Instância | Método | HV médio ± desvio amostral | Tempo médio (s) | Execuções viáveis |",
        "| --- | --- | --- | --- | --- |",
    ]
    for grupo in resumo:
        texto.append(f"| {grupo['instancia']} | {grupo['metodo']} | "
                     f"{grupo['hv_media']:.6f} ± {grupo['hv_desvio_amostral']:.6f} | "
                     f"{grupo['tempo_medio_segundos']:.3f} | "
                     f"{grupo['com_solucao_viavel']}/{grupo['execucoes']} |")
    texto.extend(["", "## Comparações por semente", "",
                  "Vitórias/empates/derrotas do MOMA em HV, usando a mesma semente numérica. "
                  "Os métodos consomem aleatoriedade de formas diferentes; isso não cria "
                  "amostras iniciais idênticas. Empate usa tolerância de 1e-12. "
                  "São contagens descritivas, sem teste de significância.", "",
                  "| Instância | Comparador | Vitórias | Empates | Derrotas |",
                  "| --- | --- | --- | --- | --- |"])
    for instancia in sorted({l["instancia"] for l in linhas}):
        moma = {l["semente"]: l["hipervolume"] for l in linhas
                if l["instancia"] == instancia and l["metodo"] == "moma"}
        for metodo in METODOS:
            vitorias = empates = derrotas = 0
            for linha in linhas:
                if linha["instancia"] != instancia or linha["metodo"] != metodo:
                    continue
                a, b = moma[linha["semente"]], linha["hipervolume"]
                if math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12):
                    empates += 1
                elif a > b:
                    vitorias += 1
                else:
                    derrotas += 1
            texto.append(f"| {instancia} | {metodo} | {vitorias} | {empates} | {derrotas} |")
    texto.extend(["", "## Interpretação e limites", "",
                  "Os arquivos por execução preservam as alocações e objetivos, e execucoes.csv "
                  "preserva as métricas. Os menores valores de cada objetivo podem pertencer "
                  "a soluções diferentes. A frente conhecida é apenas a didática; nas instâncias "
                  "maiores, não há prova de otimalidade.", "",
                  "Os gulosos mantêm o mínimo de réplicas e incluem no orçamento as avaliações "
                  "de soluções parciais. Busca aleatória e MOMA podem usar réplicas extras. "
                  "Os comparadores guardam todos os pontos não dominados avaliados, enquanto "
                  "o MOMA publica a frente da população final limitada. Orçamento igual "
                  "não significa tempo, memória ou espaço efetivamente explorado iguais.", "",
                  "O artigo reporta melhorias de utilização frente ao Kubernetes em um ambiente "
                  "real. O HV local não é a mesma métrica, e os dados de rede e os comparadores "
                  "são diferentes. Portanto, os resultados permitem classificar o MOMA adaptado "
                  "frente aos métodos locais, mas não permitem afirmar que reproduz, supera ou "
                  "fica abaixo dos ganhos percentuais publicados no artigo.", ""])
    (destino / "analise.md").write_text("\n".join(texto), encoding="utf-8")


def rodar(caminhos: list[Path], destino: Path, parametros: Parametros, sementes: list[int]) -> None:
    if not caminhos or not sementes or len(set(sementes)) != len(sementes):
        raise ValueError("Informe instâncias e sementes distintas.")
    if len({p.stem for p in caminhos}) != len(caminhos):
        raise ValueError("Os arquivos de instância devem ter nomes distintos.")
    if (destino / "manifesto.json").exists():
        raise ValueError("Diretório já possui experimento. Escolha outra --saida para preservar os resultados.")
    arquivos_codigo = [RAIZ / 'codigo' / nome for nome in (
        "modelo.py", "moma.py", "comparadores.py", "metricas.py", "gerar_instancias.py", "experimentos.py")]
    arquivos_dados = [RAIZ / "dados" / "recursos_artigo.json", *caminhos]
    manifesto = {
        "python": platform.python_version(), "sistema": platform.platform(),
        "processador": platform.processor(), "modelo": "moma-operacional-v1",
        "parametros_moma": asdict(parametros), "sementes": sementes,
        "metodos": ["moma", *METODOS],
        "orcamento_por_execucao": parametros.populacao + parametros.geracoes * parametros.descendentes,
        "sha256": {str(p.relative_to(RAIZ)) if p.is_relative_to(RAIZ) else str(p):
                   hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in arquivos_codigo + arquivos_dados},
    }
    # Carrega e valida todas as instâncias antes de iniciar as execuções.
    instancias = [(p, carregar_instancia(p)) for p in caminhos]
    salvar_json(destino / "manifesto.json", manifesto)
    linhas = []
    for caminho, instancia in instancias:
        for semente in sementes:
            for metodo in ("moma", *METODOS):
                if metodo == "moma":
                    resultado = executar(instancia, replace(parametros, semente=semente))
                else:
                    resultado = executar_comparador(instancia, metodo,
                                                    manifesto["orcamento_por_execucao"], semente)
                if resultado["avaliacoes"] != manifesto["orcamento_por_execucao"]:
                    raise RuntimeError("Orçamento de avaliações divergente.")
                for solucao in resultado["fronteira"]:
                    av = avaliar(instancia, solucao["alocacao"])
                    if not av.viavel or list(av.objetivos) != solucao["objetivos"]:
                        raise RuntimeError("Solução publicada não confere com o avaliador.")
                metricas = medir(instancia, resultado["pontos_nao_dominados"])
                resultado["metricas"] = metricas
                salvar_json(destino / "execucoes" / caminho.stem / metodo / f"semente_{semente}.json", resultado)
                linhas.append({
                    "instancia": instancia.nome, "metodo": metodo, "semente": semente,
                    "avaliacoes": resultado["avaliacoes"],
                    "tempo_segundos": resultado["tempo_segundos"],
                    "hipervolume": metricas["hipervolume"], "pontos": metricas["pontos"],
                    "menor_balanceamento": metricas["menor_balanceamento"],
                    "menor_comunicacao": metricas["menor_comunicacao"],
                })
            print(f"Concluído: {caminho.stem}, semente {semente}, quatro métodos.", flush=True)
    resumir(linhas, destino)
    print(f"Resultados e análise: {destino}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instancias", type=Path, nargs="+",
                        default=sorted((RAIZ / "dados" / "experimentos").glob("*.json")))
    parser.add_argument("--saida", type=Path, default=RAIZ / "resultados" / "experimentos")
    parser.add_argument("--sementes", type=int, nargs="+", default=list(range(10)))
    parser.add_argument("--populacao", type=int, default=40)
    parser.add_argument("--descendentes", type=int, default=40)
    parser.add_argument("--geracoes", type=int, default=40)
    args = parser.parse_args()
    try:
        parametros = Parametros(populacao=args.populacao, descendentes=args.descendentes,
                                geracoes=args.geracoes)
        rodar(args.instancias, args.saida, parametros, args.sementes)
    except (OSError, ValueError) as erro:
        parser.exit(2, f"Erro: {erro}\n")


if __name__ == "__main__":
    main()
