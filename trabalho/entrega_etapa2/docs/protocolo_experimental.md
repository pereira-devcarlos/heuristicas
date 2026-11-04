# Protocolo dos experimentos locais

## Objetivo e alcance

Avaliar o MOMA adaptado frente a três comparadores simples no mesmo modelo
operacional. Estes experimentos são simulações de alocação, sem executar
contêineres ou coletar medições de desempenho em Kubernetes. A implementação
e as escolhas de modelagem estão em `modelo_operacional.md`.

## Construção das seis instâncias

As demandas de CPU e memória das Tabelas 4 e 5 de Chen e Wen (2024), páginas
7422–7423, foram transcritas em `dados/recursos_artigo.json`. São nove serviços
no EdgeX Foundry, 14 no Sock Shop e 14 no Kubeflow. Cada aplicação possui dois
cenários de demanda, correspondentes a um e dez usuários. Não interpolamos
os valores e preservamos as diferenças não monotônicas entre as cargas.
Os nomes dos serviços seguem a tabela, inclusive `tran-pipeline`.

Cada instância é **híbrida**: os valores de CPU e memória são publicados, enquanto
todos os elementos abaixo são sintéticos. Não são as instâncias originais do artigo.

### Infraestrutura

Seis nós em três clusters: n0/n1 em c0, n2/n3 em c1 e n4/n5 em c2.
O dimensionamento é fixado pela demanda de dez usuários da respectiva aplicação
e mantido nos cenários de um e dez usuários.

Para CPU e memória separadamente, usamos as frações
`[1.05, 0.25, 0.60, 0.20, 0.70, 0.35]` do total exigido por uma réplica de cada
serviço na carga de dez usuários. Nos nós pares, a capacidade também deve ser
pelo menos 1,05 vezes a maior demanda individual do recurso. Os valores são
arredondados a seis casas decimais. São capacidades lógicas sintéticas: não
afirmamos que correspondem a modelos comerciais de processadores ou memórias.

As seis instâncias têm uma testemunha viável, conferida nos testes: uma réplica
de cada serviço no nó n0. Isso assegura que ausência de solução viável em uma
execução não seja confundida com inviabilidade física da instância. A testemunha
não é inserida na população nem fornecida aos comparadores.

Cada nó recebe taxa de falha uniforme em [0,01; 0,03]. A distância é simétrica,
com diagonal zero: uniforme em [1; 1,5] dentro do cluster e [2,5; 4] entre clusters.
Esses intervalos estão contidos nos intervalos considerados pelo artigo, mas
os sorteios específicos e a separação intra/intercluster são hipóteses locais.

### Comunicação e réplicas

As interações são dirigidas e não utilizam a coluna Interaction do artigo.
Os serviços são ordenados como nas tabelas e divididos em grupos consecutivos
de até três. Um arco entre serviços distintos é criado com probabilidade 0,65
no mesmo grupo e 0,10 em grupos diferentes. Além disso, sempre incluímos um
anel dirigido, do serviço i ao próximo, com retorno do último ao primeiro.
Os grupos são uma construção sintética, não dependências identificadas das aplicações.

Cada arco recebe volume base uniforme em [1; 10], multiplicado pela quantidade
de usuários. O crescimento linear do tráfego é uma hipótese sintética, sem
pretensão de representar as medições originais. O volume está em unidades
arbitrárias de dados por segundo. Os serviços admitem de uma a duas réplicas.

O gerador usa `random.Random` e sementes 101 (EdgeX), 102 (Sock Shop) e 103
(Kubeflow). Para cada aplicação, infraestrutura, falhas, distâncias e grafo base
são iguais entre as duas cargas. O gerador é determinístico no ambiente testado,
e os JSONs completos são entregues, dispensando regeneração para executar a busca.

## Métodos comparados

| Método | Procedimento |
| --- | --- |
| MOMA adaptado | População, torneio binário, SBX inteiro com reparo, inserção/remoção e seleção ambiental NSGA-II |
| Busca aleatória | Usa a mesma inicialização aleatória do MOMA em cada amostra, sem seleção evolutiva |
| Guloso de recursos | Insere as réplicas mínimas em ordem sorteada e escolhe cada nó por violação, depois balanceamento, depois comunicação |
| Guloso de comunicação | Usa a mesma construção, mas escolhe por violação, depois comunicação, depois balanceamento |

Nos gulosos, a lista de inserções contém o mínimo de réplicas de todos os
serviços. A ordem é embaralhada em cada reinício. Para cada inserção, avaliamos
os nós candidatos, empatando por sorteio. As soluções parciais são avaliadas com
o mesmo avaliador, inclusive a penalidade por serviços ainda ausentes; essa
parcela é igual entre os nós candidatos da mesma etapa. A capacidade física
também entra na violação e, portanto, influencia a prioridade.

Os gulosos recomeçam até consumir o orçamento. Se ele acabar no meio de uma
construção ou da lista de nós candidatos, a execução para sem avaliações extras.
Toda solução completa viável avaliada, mesmo se não escolhida para continuar a
construção, pode entrar no arquivo de pontos não dominados. Não publicamos
soluções incompletas como viáveis.

Busca aleatória e gulosos mantêm todos os pontos viáveis não dominados avaliados,
com uma alocação por par de objetivos. O MOMA usa a frente da população final.
São diferenças entre os métodos, declaradas para interpretar a comparação.
Os comparadores **não são** reimplementações do Kubernetes, Multiopt ou Greedy
usados pelos autores do artigo.

## Configuração e orçamento

| Parâmetro | Valor |
| --- | --- |
| População do MOMA | 40 |
| Descendentes por geração | 40 |
| Gerações | 40 |
| Probabilidade de cruzamento | 0,5 |
| Probabilidade de mutação do par | 0,3 |
| Probabilidade de inserção ou remoção | 0,5 cada |
| Índice SBX eta | 10 |
| Sementes de execução | 0 a 9 |
| Orçamento por execução, para todos os métodos | 40 + 40 × 40 = 1.640 avaliações |

São 240 execuções e 393.600 avaliações de busca no total. A contagem inclui
indivíduos repetidos, soluções inviáveis e, nos gulosos, os candidatos parciais.
A reavaliação das soluções publicadas para auditoria ocorre depois da busca e
não retroalimenta a seleção nem entra no orçamento. A medição do tempo cobre
a busca e a formação de sua saída, excluindo gravação de arquivo e auditoria.
Todos os métodos são executados sequencialmente na mesma máquina.

O orçamento e os tamanhos populacionais foram escolhidos para uma bateria local
reproduzível. São diferentes da população/descendentes 200 da Tabela 3 e do
critério 25.000 do artigo. Não foram ajustados retrospectivamente para favorecer
um método. Mesma semente numérica não significa mesmas amostras entre métodos.
Orçamento igual de avaliações também não significa igualdade de tempo ou memória.

## Hipervolume

Ambos os objetivos são minimizados. Para comparar frentes, usamos hipervolume
bidimensional, calculado como a área da união dos retângulos entre os pontos
e uma referência comum. Pontos dominados ou repetidos não aumentam a área.

O objetivo de recursos é uma média ponderada de razões de uso, seguida do máximo;
em uma solução viável, fica em [0; 1]. A comunicação é normalizada por:

```text
escala = max(1, soma_dos_volumes * maior_distancia * (1 + maior_falha))
comunicacao_normalizada = comunicacao / escala
```

O limite é conservador, pois as frações de tráfego de cada interação somam um
entre todos os pares de nós, e a comunicação local não contribui. Assim, o
segundo objetivo normalizado também está em [0; 1]. A referência é `(1.1, 1.1)`,
fixa para todos os métodos e sementes, e a área máxima teórica é 1,21.
A escala depende somente da instância, nunca da qualidade das soluções encontradas.
O ponto de referência deve ser estritamente maior que todos os pontos usados;
o código rejeita uma violação dessa regra, sem recortar os pontos silenciosamente.

HV maior é melhor. Uma execução sem solução viável recebe HV zero.
As médias, medianas e desvios padrão amostrais são calculados sobre as dez
execuções, incluindo esses zeros. Reportamos também a quantidade de execuções
com pelo menos uma solução viável, cardinalidade da frente, tempo e mínimos de
cada objetivo. Os dois mínimos não precisam pertencer à mesma solução.

O hipervolume é uma métrica de cobertura dentro de cada instância. Não é um
percentual de utilização e não deve ser comparado diretamente com os percentuais
publicados pelos autores, nem usado para ranquear a dificuldade de instâncias
distintas sem considerar suas diferentes escalas e conjuntos viáveis.

## Reprodutibilidade e análise

`resultados/experimentos/manifesto.json` registra parâmetros, sementes, ambiente
Python/sistema e hashes SHA-256 do código utilizado, demandas transcritas e
instâncias. Cada execução tem um JSON com alocações e objetivos; a bateria confere
novamente a viabilidade e o valor dos objetivos antes de salvar.
`execucoes.csv` contém os valores por execução, `resumo.json` contém agregações
e `analise.md` apresenta tabelas descritivas.

O comando recusa sobrescrever um diretório com manifesto existente. Para uma
nova bateria, informe outro diretório com `--saida`. Não execute mais de uma
bateria simultaneamente no mesmo diretório. Alterações de código exigem uma
nova bateria para que o manifesto continue identificando a versão avaliada.

As contagens de vitórias, empates e derrotas em HV são descritivas. Não aplicamos
teste de significância e não alegamos superioridade estatística ou generalização
para outros grafos, infraestruturas ou volumes. O experimento usa um único grafo
sintético por aplicação. Os resultados não medem requisições falhas, latência,
vazão, consumo energético ou confiabilidade real.

Em particular, a comparação com o artigo deve reconhecer que mudaram instâncias,
modelagem, orçamento, infraestrutura e comparadores. É possível discutir tendências
e resultados locais melhores, piores ou similares, mas não determinar a reprodução
numérica dos ganhos do MOMA original sem dados e experimentos equivalentes.
