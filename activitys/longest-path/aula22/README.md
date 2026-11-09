# Aula 22 — Caminho mais longo biobjetivo com NSGA-II

## Organização dos arquivos

- `main.py`: leitura das instâncias, execução e exportação dos resultados.
- `heuristics.py`: decodificador e operadores do NSGA-II.
- `generator.py`: geração e conversão de instâncias biobjetivo.
- `test_nsga2.py`: testes automatizados.
- `instancias/`: três instâncias de exemplo reproduzíveis.
- `aula22.md` e `caminhoMaisLongoBiobjetivo.pdf`: enunciado e definição do problema.

A pasta `resultados/`, os caches Python e os arquivos ZIP são ignorados pelo
Git. Nos comandos abaixo, os resultados são salvos em `aula22/resultados/`.

## Raciocínio e relação com a aula 18

Na aula 18, o BRKGA avalia cada caminho por um único custo. Aqui cada
aresta possui dois pesos, e avaliamos o caminho pelas somas `(W1, W2)`.
Ambas devem ser maximizadas, entre quaisquer extremos, sem repetir vértices.

Um caminho domina outro quando é pelo menos tão bom nos dois objetivos e
estritamente melhor em pelo menos um. Por exemplo, `(10, 8)` domina `(9, 7)`,
mas `(10, 5)` e `(6, 9)` são incomparáveis. Vetores iguais não se dominam.
Não somamos os objetivos para decidir qual solução vence.

Mantemos a separação entre cromossomo e caminho da aula 18. Há `n+2` chaves:

- `n` prioridades: escolhem o vizinho ainda não visitado de menor chave;
- uma chave seleciona o início dentre os vértices com vizinhos;
- uma chave determina o limite de arestas, entre `1` e `n-1`.

A construção termina nesse limite ou quando não há vizinho disponível.
Ela sempre produz um caminho simples com pelo menos uma aresta. O limite
variável permite representar caminhos curtos mesmo com pesos negativos;
não aproveitamos a regra mono-objetivo de escolher um único melhor prefixo.
O decoder é determinístico e não favorece explicitamente nenhum objetivo.

O NSGA-II executa:

1. Inicialização aleatória e avaliação dos dois objetivos.
2. Ordenação em frentes de não dominância (menor rank é melhor).
3. Cálculo da distância de aglomeração normalizada por objetivo. Distâncias
   maiores favorecem regiões menos povoadas; os extremos são preservados.
4. Seleção dos pais por torneio: rank, depois distância, depois sorteio.
5. Cruzamento uniforme e mutação independente por gene, com taxa `1/(n+2)`.
6. União dos N pais com N filhos e seleção dos próximos N indivíduos.

Esta implementação usa chaves aleatórias com NSGA-II, conforme permitido no
enunciado. Não aplica a divisão elite/não elite nem o cruzamento tendencioso
do BRKGA clássico. Não precisa da biblioteca C++ usada na aula 18.
A ordenação não dominada tem custo quadrático no tamanho da população.

## Executar

Use Python 3.10 ou superior, sem dependências adicionais. A partir da raiz:

```bash
python aula22/main.py aula22/instancias/conflitante-20-42.txt --population 100 --generations 100 --seed 42 --output aula22/resultados
```

O programa salva um representante por vetor objetivo não dominado da população
final: CSV com pesos e caminhos, JSON com parâmetros/tempo/avaliações e SVG com
o gráfico. Abra o SVG no navegador. A fronteira é uma aproximação: não existe
garantia de ótimo global. Não há arquivo externo de todas as soluções visitadas;
um ponto encontrado antes pode ser descartado por falta de espaço na população.

As instâncias usam vértices de `0` a `n-1`, em grafo não direcionado:

```text
n m
u v peso1 peso2
```

## Gerar novas instâncias

```bash
python aula22/generator.py --nodes 50 --probability 0.15 --seed 42 --mode independent --output aula22/instancias/nova.txt
python aula22/generator.py --nodes 50 --probability 0.15 --seed 42 --mode conflicting --output aula22/instancias/nova-conflitante.txt
python aula22/generator.py --source codeBase/instancias/regular-1000-1 --seed 42 --output aula22/instancias/regular-bi.txt
```

O gerador próprio começa com uma árvore e acrescenta arestas com a probabilidade
informada. Assim, garante conexão; não é exatamente o modelo Erdős–Rényi.
A conversão mantém a topologia e o primeiro peso da instância original.
No modo independente, o segundo peso é uniforme inteiro entre 1 e 100;
no conflitante, é `mínimo(W1) + máximo(W1) - W1` por aresta.
Isso cria oposição por aresta, mas não garante oposição nas somas dos caminhos,
pois caminhos maiores podem ganhar nos dois objetivos. Três instâncias pequenas
reproduzíveis estão incluídas para começar os experimentos.

## Questões para discussão

**Como comparar resultados?** Execute várias sementes com a mesma instância e
os mesmos parâmetros; reporte tempo, número de avaliações e dispersão. O número
de pontos sozinho não mede qualidade. Para populações/algoritmos diferentes,
fixe o orçamento de avaliações ou tempo. Verifique se as soluções de uma
execução dominam as de outra. Pode-se também usar hipervolume, com um mesmo
ponto de referência dominado e escalas consistentes em todas as execuções;
essa métrica, maior é melhor. O cálculo de hipervolume não está implementado.

Em instâncias pequenas, compare com enumeração exata. Em instâncias grandes,
a união não dominada de várias execuções serve como referência empírica,
sem provar que seja a fronteira verdadeira. Repetir a semente reproduz os
resultados com o mesmo ambiente e parâmetros, exceto o tempo medido.

**Como visualizar?** No SVG, cada ponto tem `W1` no eixo horizontal e `W2` no
vertical. Como ambos são maximizados, buscamos pontos mais acima e à direita.
Os pontos não são ligados: segmentos entre caminhos não representam soluções
necessariamente viáveis. Para sobrepor execuções em uma planilha, importe os
CSVs como dispersão XY, usando uma cor por semente e os mesmos limites dos eixos.

## Validação

```bash
python -m unittest discover -s aula22 -v
```

Os testes verificam dominância e empates, ranks, preservação dos extremos,
reprodutibilidade, vértices isolados e pesos negativos. Em um triângulo,
enumeram todos os caminhos para comparar a aproximação com a fronteira exata,
além de conferir os pesos e a ausência de vértices repetidos.
