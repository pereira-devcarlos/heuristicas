# Trabalho final — Heurísticas e Metaheurísticas

**Etapa 2: implementação e avaliação do MOMA**  
Autor: Carlos Eduardo Pereira dos Santos  
Matrícula: 2024.2.08.001  
UNIFAL-MG — Bacharelado em Ciência da Computação  
Disciplina: DCE770 — Heurísticas e metaheurísticas  
Professor: Iago Augusto de Carvalho

## Organização

```text
README.md                  Instruções de execução
executar.py                Comando principal
codigo/                    Algoritmo, comparadores e scripts
dados/                     Instâncias completas e demandas transcritas
testes/                    Testes automatizados
relatorio/
    relatorio.pdf          Documento formatado para leitura
    relatorio.md           Texto editável
docs/                      Modelo operacional e protocolo experimental
resultados/
    validacao/             Referência exata da instância pequena
    experimentos/
        analise.md         Tabelas e comparação dos métodos
        execucoes.csv      Métricas das 240 execuções
        resumo.json        Agregações por cenário e método
        manifesto.json     Registro original da bateria experimental
        reorganizacao.json Mapa dos caminhos e hashes após reorganização
        execucoes/         Resultados separados por cenário, método e semente
ARQUIVOS.sha256            Integridade dos arquivos entregues
```

## Requisitos

Python **3.10 ou superior**. A busca e os testes usam apenas a biblioteca padrão:
não há dependências a instalar nem etapa de compilação. Execute os comandos
abaixo na pasta onde estão este README e `executar.py`, após extrair o ZIP.

## Execução rápida

Para executar o MOMA na instância didática:

```bash
python3 executar.py moma dados/pequena.json --populacao 20 --descendentes 20 --geracoes 20 --semente 0
```

Para salvar uma execução:

```bash
python3 executar.py moma dados/pequena.json --populacao 20 --descendentes 20 --geracoes 20 --semente 0 --saida resultados/minha_execucao.json
```

O JSON contém parâmetros, semente, quantidade de avaliações, tempo, histórico e
alocações viáveis não dominadas. Os índices das matrizes seguem a ordem dos serviços
e nós nas listas da instância. Uma fronteira vazia significa que a execução não
encontrou solução viável; não prova inviabilidade da instância.

Sem opções de tamanho, o comando `moma` usa população 200, descendentes 200 e
100 gerações. Aceita `--prob-cruzamento`, `--prob-mutacao`, `--eta` e `--semente`.
O orçamento é `populacao + geracoes * descendentes`. A semente permite repetir
os resultados no mesmo ambiente, com variação no tempo medido. O padrão de
100 gerações é de desenvolvimento e difere do critério 25.000 do artigo.

## Validação e testes

```bash
python3 -m unittest discover -s testes -v
python3 executar.py enumerar dados/pequena.json
python3 executar.py validar dados/pequena.json --saida resultados/nova_validacao.json
```

São **39 testes**. A enumeração didática contém 25 alocações, 11 viáveis e os
pontos exatos `(0.50, 30.90)` e `(0.75, 0)` na fronteira. O comando `validar`
compara a busca à enumeração em vinte sementes. Ele pode ser utilizado apenas
com instâncias pequenas, devido ao custo da enumeração exata.

## Reprodução dos experimentos

Os resultados entregues já estão em `resultados/experimentos`. Para repetir
a bateria preservando esses arquivos:

```bash
python3 -u -m codigo.experimentos --saida resultados/reexecucao
```

São seis cenários, dez sementes e quatro métodos: MOMA, busca aleatória,
guloso de recursos e guloso de comunicação. A configuração é população 40,
descendentes 40 e 40 gerações, com 1.640 avaliações por execução, totalizando
240 execuções e 393.600 avaliações. O tempo depende do computador. O comando
recusa sobrescrever uma bateria cujo diretório já contenha `manifesto.json`.

Para uma verificação reduzida:

```bash
python3 -u -m codigo.experimentos --instancias dados/experimentos/edgex_10.json --sementes 0 1 --populacao 10 --descendentes 10 --geracoes 5 --saida resultados/verificacao_rapida
```

Para reconstruir as instâncias com as mesmas regras determinísticas:

```bash
python3 -m codigo.gerar_instancias
```

## Relatório e documentação

Comece por [relatorio/relatorio.pdf](relatorio/relatorio.pdf). As definições e
hipóteses estão em [docs/modelo_operacional.md](docs/modelo_operacional.md), e
as regras da bateria em [docs/protocolo_experimental.md](docs/protocolo_experimental.md).
O resumo do artigo integra a fundamentação do relatório desta etapa.

Os dados maiores são híbridos: CPU e memória foram transcritas do artigo;
infraestrutura, rede, tráfego e limites de réplicas são sintéticos. Os comparadores
são locais e não representam Kubernetes, Multiopt ou o Greedy original.
O MOMA apresentou hipervolume médio superior ao aleatório nos seis cenários e
desempenho misto frente aos gulosos. O relatório delimita a comparação com o artigo.

O manifesto original e os resultados foram preservados. `reorganizacao.json`
relaciona os caminhos e hashes originais aos da entrega: somente os caminhos,
as importações dos testes e a organização dos arquivos de saída foram adaptados.
Novas baterias registram automaticamente os caminhos desta estrutura.
