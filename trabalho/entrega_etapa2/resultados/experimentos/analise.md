# Resultados dos experimentos locais

Instâncias híbridas: CPU e memória das Tabelas 4 e 5 de Chen e Wen (2024); infraestrutura, rede, tráfego e limites de réplicas sintéticos. Os comparadores são implementações locais, não os algoritmos originais do artigo.

O hipervolume (HV) usa minimização e referência normalizada (1,1; 1,1). CPU/memória geram objetivo de recursos no intervalo [0; 1] para soluções viáveis; comunicação é dividida por um limite conservador obtido da instância. HV maior indica melhor cobertura no modelo local. Não é percentual de utilização.

| Instância | Método | HV médio ± desvio amostral | Tempo médio (s) | Execuções viáveis |
| --- | --- | --- | --- | --- |
| edgex_10_usuarios_hibrida | moma | 0.480974 ± 0.053074 | 2.140 | 10/10 |
| edgex_10_usuarios_hibrida | aleatorio | 0.385372 ± 0.033309 | 1.743 | 10/10 |
| edgex_10_usuarios_hibrida | guloso_recursos | 0.552266 ± 0.032915 | 1.133 | 10/10 |
| edgex_10_usuarios_hibrida | guloso_comunicacao | 0.583480 ± 0.028650 | 1.079 | 10/10 |
| edgex_1_usuarios_hibrida | moma | 0.903656 ± 0.038625 | 1.963 | 10/10 |
| edgex_1_usuarios_hibrida | aleatorio | 0.778961 ± 0.047516 | 1.517 | 10/10 |
| edgex_1_usuarios_hibrida | guloso_recursos | 0.795024 ± 0.064681 | 0.977 | 10/10 |
| edgex_1_usuarios_hibrida | guloso_comunicacao | 1.042075 ± 0.009795 | 0.973 | 10/10 |
| kubeflow_10_usuarios_hibrida | moma | 0.343800 ± 0.059698 | 2.471 | 10/10 |
| kubeflow_10_usuarios_hibrida | aleatorio | 0.280649 ± 0.021420 | 1.933 | 10/10 |
| kubeflow_10_usuarios_hibrida | guloso_recursos | 0.368448 ± 0.024277 | 1.256 | 10/10 |
| kubeflow_10_usuarios_hibrida | guloso_comunicacao | 0.342875 ± 0.015700 | 1.190 | 10/10 |
| kubeflow_1_usuarios_hibrida | moma | 0.529781 ± 0.037570 | 2.207 | 10/10 |
| kubeflow_1_usuarios_hibrida | aleatorio | 0.462769 ± 0.022527 | 1.861 | 10/10 |
| kubeflow_1_usuarios_hibrida | guloso_recursos | 0.614071 ± 0.029378 | 1.122 | 10/10 |
| kubeflow_1_usuarios_hibrida | guloso_comunicacao | 0.699038 ± 0.014647 | 1.057 | 10/10 |
| sockshop_10_usuarios_hibrida | moma | 0.431243 ± 0.057186 | 2.384 | 10/10 |
| sockshop_10_usuarios_hibrida | aleatorio | 0.288766 ± 0.025509 | 1.964 | 10/10 |
| sockshop_10_usuarios_hibrida | guloso_recursos | 0.476678 ± 0.018569 | 1.199 | 10/10 |
| sockshop_10_usuarios_hibrida | guloso_comunicacao | 0.506685 ± 0.046551 | 1.175 | 10/10 |
| sockshop_1_usuarios_hibrida | moma | 0.683824 ± 0.050744 | 2.597 | 10/10 |
| sockshop_1_usuarios_hibrida | aleatorio | 0.552319 ± 0.021313 | 2.235 | 10/10 |
| sockshop_1_usuarios_hibrida | guloso_recursos | 0.629872 ± 0.026168 | 1.319 | 10/10 |
| sockshop_1_usuarios_hibrida | guloso_comunicacao | 0.918673 ± 0.010426 | 1.285 | 10/10 |

## Comparações por semente

Vitórias/empates/derrotas do MOMA em HV, usando a mesma semente numérica. Os métodos consomem aleatoriedade de formas diferentes; isso não cria amostras iniciais idênticas. Empate usa tolerância de 1e-12. São contagens descritivas, sem teste de significância.

| Instância | Comparador | Vitórias | Empates | Derrotas |
| --- | --- | --- | --- | --- |
| edgex_10_usuarios_hibrida | aleatorio | 9 | 0 | 1 |
| edgex_10_usuarios_hibrida | guloso_recursos | 0 | 0 | 10 |
| edgex_10_usuarios_hibrida | guloso_comunicacao | 0 | 0 | 10 |
| edgex_1_usuarios_hibrida | aleatorio | 9 | 0 | 1 |
| edgex_1_usuarios_hibrida | guloso_recursos | 9 | 0 | 1 |
| edgex_1_usuarios_hibrida | guloso_comunicacao | 0 | 0 | 10 |
| kubeflow_10_usuarios_hibrida | aleatorio | 9 | 0 | 1 |
| kubeflow_10_usuarios_hibrida | guloso_recursos | 3 | 0 | 7 |
| kubeflow_10_usuarios_hibrida | guloso_comunicacao | 5 | 0 | 5 |
| kubeflow_1_usuarios_hibrida | aleatorio | 9 | 0 | 1 |
| kubeflow_1_usuarios_hibrida | guloso_recursos | 0 | 0 | 10 |
| kubeflow_1_usuarios_hibrida | guloso_comunicacao | 0 | 0 | 10 |
| sockshop_10_usuarios_hibrida | aleatorio | 10 | 0 | 0 |
| sockshop_10_usuarios_hibrida | guloso_recursos | 3 | 0 | 7 |
| sockshop_10_usuarios_hibrida | guloso_comunicacao | 1 | 0 | 9 |
| sockshop_1_usuarios_hibrida | aleatorio | 10 | 0 | 0 |
| sockshop_1_usuarios_hibrida | guloso_recursos | 9 | 0 | 1 |
| sockshop_1_usuarios_hibrida | guloso_comunicacao | 0 | 0 | 10 |

## Interpretação e limites

Os arquivos por execução preservam as alocações e objetivos, e execucoes.csv preserva as métricas. Os menores valores de cada objetivo podem pertencer a soluções diferentes. A frente conhecida é apenas a didática; nas instâncias maiores, não há prova de otimalidade.

Os gulosos mantêm o mínimo de réplicas e incluem no orçamento as avaliações de soluções parciais. Busca aleatória e MOMA podem usar réplicas extras. Os comparadores guardam todos os pontos não dominados avaliados, enquanto o MOMA publica a frente da população final limitada. Orçamento igual não significa tempo, memória ou espaço efetivamente explorado iguais.

O artigo reporta melhorias de utilização frente ao Kubernetes em um ambiente real. O HV local não é a mesma métrica, e os dados de rede e os comparadores são diferentes. Portanto, os resultados permitem classificar o MOMA adaptado frente aos métodos locais, mas não permitem afirmar que reproduz, supera ou fica abaixo dos ganhos percentuais publicados no artigo.
