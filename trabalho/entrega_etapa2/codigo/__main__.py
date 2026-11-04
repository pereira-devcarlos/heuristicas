"""Execute na raiz: python3 -m codigo enumerar CAMINHO_DA_INSTANCIA."""

import argparse
import json
from pathlib import Path

from .exato import enumerar
from .modelo import carregar_instancia
from .moma import Parametros, executar
from .validacao import validar


def main():
    parser = argparse.ArgumentParser(description="Validação do modelo de alocação do MOMA.")
    comandos = parser.add_subparsers(dest="comando", required=True)
    exato = comandos.add_parser("enumerar", help="Obter a fronteira exata de instância pequena.")
    exato.add_argument("instancia", type=Path)
    exato.add_argument("--limite", type=int, default=100_000)
    exato.add_argument("--saida", type=Path)
    moma = comandos.add_parser("moma", help="Executar busca evolutiva com NSGA-II.")
    moma.add_argument("instancia", type=Path)
    moma.add_argument("--populacao", type=int, default=200)
    moma.add_argument("--descendentes", type=int, default=200)
    moma.add_argument("--geracoes", type=int, default=100)
    moma.add_argument("--prob-cruzamento", type=float, default=0.5)
    moma.add_argument("--prob-mutacao", type=float, default=0.3)
    moma.add_argument("--eta", type=float, default=10)
    moma.add_argument("--semente", type=int, default=0)
    moma.add_argument("--saida", type=Path)
    validacao = comandos.add_parser("validar", help="Comparar várias sementes à enumeração exata.")
    validacao.add_argument("instancia", type=Path)
    validacao.add_argument("--sementes", type=int, nargs="+", default=list(range(20)))
    validacao.add_argument("--populacao", type=int, default=20)
    validacao.add_argument("--descendentes", type=int, default=20)
    validacao.add_argument("--geracoes", type=int, default=20)
    validacao.add_argument("--limite", type=int, default=100_000)
    validacao.add_argument("--saida", type=Path)
    args = parser.parse_args()
    try:
        instancia = carregar_instancia(args.instancia)
        if args.comando == "enumerar":
            if args.limite < 1:
                raise ValueError("O limite de enumeração deve ser positivo.")
            resultado = enumerar(instancia, args.limite)
        elif args.comando == "moma":
            parametros = Parametros(args.populacao, args.descendentes, args.geracoes,
                                    args.prob_cruzamento, args.prob_mutacao, args.eta,
                                    args.semente)
            resultado = executar(instancia, parametros)
        else:
            if args.limite < 1:
                raise ValueError("O limite de enumeração deve ser positivo.")
            parametros = Parametros(populacao=args.populacao, descendentes=args.descendentes,
                                    geracoes=args.geracoes)
            resultado = validar(instancia, parametros, args.sementes, args.limite)
        texto = json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False)
        if args.saida:
            args.saida.parent.mkdir(parents=True, exist_ok=True)
            args.saida.write_text(texto + "\n", encoding="utf-8")
        print(texto)
    except (ValueError, OSError) as erro:
        parser.exit(2, f"Erro: {erro}\n")


if __name__ == "__main__":
    main()
