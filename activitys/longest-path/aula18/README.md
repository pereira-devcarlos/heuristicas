# Executar a resolução da aula 18

É necessário ter `git`, `g++` com suporte a C++11 e `make`. Para executar pelo `main.py`, também é necessário Python 3.10 ou superior.

## Preparar e compilar

Após extrair o ZIP, abra um terminal na pasta que contém o `Makefile` e execute:

```bash
git clone https://github.com/rfrancotoso/brkgaAPI.git external/brkgaAPI
git -C external/brkgaAPI checkout c0c6460a37db396eaf9094869a002ece97c61583
make
```

A biblioteca BRKGA e os arquivos de instância não estão incluídos no ZIP.

## Executar

Para usar uma instância disponível em qualquer pasta:

```bash
./brkga /caminho/da/instancia 100 42
```

Os dois últimos argumentos são o número de gerações e a semente aleatória. Se omitidos, os valores padrão são 100 e 0.

O arquivo de instância deve ter `n m` na primeira linha e, em seguida, `m` linhas no formato `u v peso`, com vértices numerados de 0 a n−1. O grafo é não direcionado.

Também é possível executar pelo Python, colocando as instâncias na pasta `../codeBase/instancias`, relativa à pasta da resolução:

```bash
python main.py regular-1000-1 brkga 100 42
```

O programa exibe o custo final, a sequência de vértices do caminho e o número de arestas.
