# Modelo operacional v1

Este documento fecha as escolhas necessárias para a primeira implementação.
São interpretações e adaptações do artigo, não detalhes confirmados pelos autores.
O código correspondente está em `codigo/modelo.py`. As escolhas abaixo
explicitam as lacunas identificadas no texto original.

## Dados e réplicas

A instância contém nós, clusters, capacidades, taxas de falha por nó, serviços,
limites de réplicas, distâncias entre todos os nós e interações dirigidas entre
serviços. A ordem das listas `servicos` e `nos` determina linhas e colunas de X.
Distâncias podem ser assimétricas e sua diagonal deve ser zero.
Cada interação é declarada uma vez por par ordenado; um fluxo de retorno precisa
de outra entrada. Volumes não representam número de solicitações que falharam.

`X[i][h]` é a quantidade inteira não negativa de réplicas do serviço i no nó h.
Cada serviço deve ter entre `replicas_min` e `replicas_max` réplicas, com mínimo
positivo. Réplicas no mesmo nó são permitidas. CPU e memória informadas no serviço
são custos fixos por réplica, independentemente da divisão do tráfego.

Essa hipótese não modela redução de CPU com divisão da carga nem capacidade de
atendimento por réplica. Logo, não permite concluir sobre latência, vazão ou ganhos
de disponibilidade por replicação. Os limites são parâmetros da instância e devem
ser justificados nos experimentos. Inserções podem mudar a distribuição de tráfego,
mas uma tendência de preferência pelo mínimo de réplicas deve ser analisada como
consequência do modelo; não há uma exigência de demanda que force réplicas extras.

## Objetivo de recursos

Para cada nó, calculamos as razões `u_cpu` e `u_mem` dividindo o total consumido
pela capacidade. Para cada cluster, calculamos os desvios padrão **populacionais**
dessas razões, incluindo os nós ociosos, a cada avaliação de um indivíduo.

```text
s = sigma_cpu_cluster + sigma_mem_cluster

se s > 0:
    peso_cpu = sigma_cpu_cluster / s
    peso_mem = sigma_mem_cluster / s
senão:
    peso_cpu = peso_mem = 0.5

carga[h] = peso_cpu[cluster(h)] * u_cpu[h]
         + peso_mem[cluster(h)] * u_mem[h]

balanceamento = max_h carga[h]
```

Isso interpreta a normalização da Equação (1) dentro do máximo, com alocação
explícita. Os pesos são calculados sobre razões de uso para evitar combinar cores
e memória diretamente. A média com pesos iguais no caso de desvio zero evita
divisão por zero e mantém a carga representada: um cluster completamente ocupado
não recebe objetivo zero apenas por estar uniforme. Um cluster com um nó também
usa pesos iguais. Essa regra de contingência é uma adaptação nossa.

Adicionalmente reportamos os desvios das razões de uso entre **todos os nós** e
`sigma_cluster = 0.5 * sqrt(sigma_cpu**2 + sigma_memoria**2)`, inspirado na
Equação (9). É uma estatística global auxiliar e não substitui o objetivo nem
reproduz automaticamente a agregação das medições experimentais do artigo.

## Objetivo de comunicação

Para cada interação dirigida i → j com volume V, o tráfego é repartido
uniformemente entre todas as réplicas de origem e de destino. Se `R[i]` é o
número total de réplicas de i, a fração encaminhada do nó h ao nó k é:

```text
fracao(i,j,h,k) = X[i][h] / R[i] * X[j][k] / R[j]
comunicacao = soma_(i,j) soma_(h != k)
              V[i,j] * fracao(i,j,h,k) * (1 + falha[h]) * distancia[h][k]
```

O fator de falha é do nó de origem. Mantemos o fator `1 + falha` do artigo;
não o substituímos por uma fórmula de retransmissões esperadas. O custo no mesmo
nó é zero. Pares entre clusters entram no mesmo cálculo, como extensão explícita
da soma impressa no artigo. Não há custo adicional de sincronização entre réplicas
além das interações que forem declaradas.

Uma linha sem réplicas torna a solução inviável; nesse caso, ignoramos suas
interações para evitar divisão por zero. O baixo custo resultante não beneficia
essa solução frente a uma viável, pois a dominância considera restrições primeiro.

## Restrições e dominância

```text
violacao = soma_h max(0, cpu_usada[h] / capacidade_cpu[h] - 1)
         + soma_h max(0, mem_usada[h] / capacidade_mem[h] - 1)
         + soma_i max(0, replicas_min[i] - R[i]) / replicas_min[i]
         + soma_i max(0, R[i] - replicas_max[i]) / replicas_max[i]
```

São viáveis as soluções com violação zero. Igualdade com a capacidade é permitida.
Uma solução viável domina uma inviável. Entre inviáveis, menor violação tem
preferência; entre viáveis, usamos dominância de Pareto estrita nos dois objetivos.
Empates não dominam um ao outro. As comparações usam os floats calculados sem
arredondamento; testes de contas manuais usam tolerância numérica.

## Instância de conferência manual

`dados/pequena.json` é inteiramente sintética. Nós a e b pertencem a clusters
distintos. Suas capacidades são (4 CPU, 8 MB) e (2 CPU, 4 MB), e suas falhas
são 0,01 e 0,03. A distância entre eles é 3.
Os serviços s0 e s1 consomem (1 CPU, 2 MB) e (2 CPU, 4 MB) por réplica;
cada um admite uma ou duas réplicas. Há um fluxo de volume 10 de s0 para s1.

| X: linhas s0/s1, colunas a/b | Balanceamento | Comunicação | Violação |
| --- | --- | --- | --- |
| `[[1,0],[1,0]]` | 0,75 | 0 | 0 |
| `[[0,1],[1,0]]` | 0,50 | 10 × 1,03 × 3 = 30,90 | 0 |
| `[[1,1],[1,0]]` | 0,75 | 5 × 1,03 × 3 = 15,45 | 0 |
| `[[0,1],[0,1]]` | 1,50 | 0 | 1 |

Na segunda linha, ambos os nós usam 50% de CPU e memória. Na terceira, metade
do tráfego permanece no nó a e a outra metade sai de b. Na última, o nó b excede
CPU e memória em 50% cada, portanto a solução é inviável.

Cada serviço admite cinco distribuições de réplicas entre os dois nós: duas com
uma réplica e três com duas. Assim, o produto cartesiano contém 25 alocações,
antes de excluir as que excedem capacidades; 11 são viáveis. A fronteira exata tem os pontos
`(0.50, 30.90)` e `(0.75, 0)`: há um compromisso real entre carga e comunicação.

A enumeração percorre somente contagens dentro dos limites de réplicas e filtra
as restrições físicas. Guarda todas as alocações viáveis não dominadas, inclusive
as que eventualmente tenham objetivos iguais, e também publica pontos distintos.
O limite padrão de 100.000 alocações impede executar a busca exaustiva em problemas
grandes por engano. Essa enumeração é uma referência de validação, não o MOMA.

## Busca evolutiva implementada

`codigo/moma.py` implementa os seguintes passos:

1. Inicialização aleatória: sorteia uniformemente o total de réplicas entre os
   limites de cada serviço; distribui cada réplica em um nó sorteado uniformemente.
   Isso não é uma amostragem uniforme das matrizes possíveis. Pode gerar sobrecarga.
2. Ordenação não dominada com restrições, seguida de crowding distance por frente.
3. Torneio binário entre dois indivíduos distintos: prefere menor rank, depois
   maior crowding distance e sorteia os empates. Os dois torneios podem escolher
   o mesmo indivíduo como pai e mãe.
4. Cruzamento SBX nas contagens com eta configurável. Um sorteio decide o
   cruzamento do par; se não ocorrer, os filhos são cópias independentes dos pais.
5. Um único sorteio decide a mutação do par, seguindo o Algoritmo 1. Quando
   ocorrer, cada filho sorteia independentemente inserção ou remoção, com 50% para
   cada operação, e altera uma contagem de um serviço elegível.
6. Seleção elitista da união de pais e filhos por frente. Se uma frente exceder
   as vagas restantes, prefere maior crowding distance, sorteando empates.
7. Repetição pelo número de gerações configurado; a saída contém somente soluções
   viáveis de rank zero da população final, sem consultar a enumeração exata.

Na crowding distance, os extremos recebem infinito e as distâncias internas são
normalizadas pela amplitude de cada objetivo. Objetivos constantes não contribuem;
frentes de até dois indivíduos recebem distância infinita. Infinito é apenas
metadado interno de seleção e não é serializado no JSON de resultados.

### Discretização e reparo

O SBX aplica as Equações (7) por célula e usa 0,5 no limiar da distribuição de
beta, separadamente da probabilidade do cruzamento. Cada contagem é limitada
ao intervalo de zero ao máximo de réplicas do serviço e arredondada por
`floor(valor + 0.5)`. Se o total da linha ultrapassar o máximo, remove-se uma
réplica de um nó ocupado sorteado até regularizar. Se ficar abaixo do mínimo,
adiciona-se uma réplica em um nó sorteado até regularizar. O reparo não procura
melhorar objetivos nem elimina sobrecargas físicas; estas seguem tratadas por
dominância por restrições. Arredondamento e reparo são adaptações nossas.

Na mutação, o serviço é sorteado uniformemente entre os elegíveis. Para inserção,
um nó é sorteado entre todos; para remoção, entre os nós ocupados pelo serviço.
Se não houver serviço elegível para a operação sorteada, a mutação não altera o
filho. Não há troca automática para outra operação. Limites mínimos e máximos
iguais bloqueiam ambas as mutações desse serviço; com contagens pequenas, o
arredondamento do SBX também pode produzir muitos filhos iguais aos pais. Essa
limitação de exploração deve ser considerada nos experimentos maiores.

Os pais não são modificados pelos operadores. A lista de filhos é reiniciada
a cada geração e tem exatamente o tamanho configurado; se esse tamanho for
ímpar, o último filho excedente do par é descartado antes de ser avaliado.
Duplicatas continuam na população, como no fluxo básico do NSGA-II.

Os padrões de população e descendentes (200), cruzamento (0,5) e mutação (0,3)
seguem a Tabela 3; eta é 10. O padrão de 100 gerações é para desenvolvimento,
não uma alegação de reprodução do critério do artigo. Todos os parâmetros
efetivos e a quantidade de avaliações são incluídos na saída.
