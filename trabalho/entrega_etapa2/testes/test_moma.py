"""Verificações do NSGA-II e comparação independente com enumeração exata."""

import math
import random
import unittest
from dataclasses import replace
from pathlib import Path

from codigo.exato import enumerar
from codigo.modelo import avaliar, carregar_instancia
from codigo.moma import (Individuo, Parametros, calcular_distancias, cruzar, executar,
                   inicializar, mutar, ordenar_frentes, selecionar_ambiente, torneio)
from codigo.validacao import mesmos_pontos, validar


class TestMoma(unittest.TestCase):
    def setUp(self):
        self.instancia = carregar_instancia(Path(__file__).resolve().parent.parent / "dados" / "pequena.json")
        self.base = avaliar(self.instancia, [[1, 0], [1, 0]])

    def individuo(self, x, y, violacao=0):
        return Individuo([[1, 0], [1, 0]],
                         replace(self.base, balanceamento=x, comunicacao=y, violacao=violacao))

    def test_frentes_com_restricoes_e_empates(self):
        populacao = [self.individuo(1, 3), self.individuo(2, 2), self.individuo(3, 1),
                     self.individuo(3, 3), self.individuo(0, 0, 1),
                     self.individuo(0, 0, 2), self.individuo(1, 3)]
        frentes = ordenar_frentes(populacao)
        self.assertEqual([len(f) for f in frentes], [4, 1, 1, 1])
        self.assertEqual([ind.rank for ind in populacao], [0, 0, 0, 1, 2, 3, 0])

    def test_distancia_normalizada_e_extremos(self):
        frente = [self.individuo(1, 5), self.individuo(2, 3), self.individuo(4, 1)]
        calcular_distancias(frente)
        self.assertTrue(math.isinf(frente[0].distancia))
        self.assertTrue(math.isinf(frente[2].distancia))
        self.assertEqual(frente[1].distancia, 2)

    def test_objetivos_constantes_nao_geram_nan(self):
        frente = [self.individuo(1, 1) for _ in range(4)]
        calcular_distancias(frente)
        self.assertEqual([ind.distancia for ind in frente], [0] * 4)

    def test_selecao_ambiental_preserva_extremos(self):
        frente = [self.individuo(1, 5), self.individuo(2, 3), self.individuo(4, 1),
                  self.individuo(5, 5)]
        selecionados = selecionar_ambiente(frente, 2, random.Random(0))
        self.assertEqual({ind.avaliacao.objetivos for ind in selecionados}, {(1, 5), (4, 1)})

    def test_torneio_prefere_rank_e_depois_distancia(self):
        melhor, pior = self.individuo(1, 1), self.individuo(2, 2)
        melhor.rank, pior.rank = 0, 1
        pior.distancia = math.inf
        self.assertIs(torneio([melhor, pior], random.Random(0)), melhor)
        pior.rank = 0
        self.assertIs(torneio([melhor, pior], random.Random(0)), pior)

    def test_operadores_preservam_limites_e_nao_alteram_pais(self):
        rng = random.Random(42)
        parametros = Parametros(prob_cruzamento=1, eta=0)
        for _ in range(100):
            pai, mae = inicializar(self.instancia, rng), inicializar(self.instancia, rng)
            copias = [[linha[:] for linha in x] for x in (pai, mae)]
            filhos = cruzar(self.instancia, pai, mae, parametros, rng)
            for filho in filhos:
                mutar(self.instancia, filho, rng)
                for linha, servico in zip(filho, self.instancia.servicos):
                    self.assertTrue(all(type(v) is int and v >= 0 for v in linha))
                    self.assertLessEqual(sum(linha), servico.replicas_max)
                    self.assertGreaterEqual(sum(linha), servico.replicas_min)
            self.assertEqual([pai, mae], copias)

    def test_insercao_e_remocao_sao_locais(self):
        tipos = set()
        for semente in range(20):
            alocacao = [[1, 0], [2, 0]]
            antes = [linha[:] for linha in alocacao]
            mutar(self.instancia, alocacao, random.Random(semente))
            diferencas = [a - b for linha_a, linha_b in zip(alocacao, antes)
                          for a, b in zip(linha_a, linha_b)]
            self.assertEqual(sum(v != 0 for v in diferencas), 1)
            tipos.add(sum(diferencas))
        self.assertEqual(tipos, {-1, 1})

    def test_cruzamento_desligado_copia_pais(self):
        pai, mae = [[1, 0], [0, 1]], [[0, 2], [1, 0]]
        filhos = cruzar(self.instancia, pai, mae, Parametros(prob_cruzamento=0), random.Random(0))
        self.assertEqual(filhos, (pai, mae))
        filhos[0][0][0] = 0
        self.assertEqual(pai[0][0], 1)

    def test_orcamento_inclui_inicializacao_e_descendentes_impares(self):
        parametros = Parametros(populacao=8, descendentes=3, geracoes=4)
        resultado = executar(self.instancia, parametros)
        self.assertEqual(resultado["avaliacoes"], 8 + 3 * 4)
        self.assertEqual(resultado["individuos_finais"], 8)
        self.assertEqual(len(resultado["historico"]), 5)

    def test_mesma_semente_reproduz_resultado_exceto_tempo(self):
        parametros = Parametros(populacao=10, descendentes=10, geracoes=5, semente=37)
        a, b = executar(self.instancia, parametros), executar(self.instancia, parametros)
        a.pop("tempo_segundos")
        b.pop("tempo_segundos")
        self.assertEqual(a, b)

    def test_fronteira_exata_em_cinco_sementes(self):
        referencia = enumerar(self.instancia)["pontos_nao_dominados"]
        for semente in range(5):
            with self.subTest(semente=semente):
                resultado = executar(self.instancia, Parametros(
                    populacao=20, descendentes=20, geracoes=20, semente=semente))
                self.assertEqual(resultado["pontos_nao_dominados"], referencia)
                for ponto in resultado["fronteira"]:
                    avaliacao = avaliar(self.instancia, ponto["alocacao"])
                    self.assertTrue(avaliacao.viavel)
                    self.assertEqual(list(avaliacao.objetivos), ponto["objetivos"])

    def test_evolucao_recupera_pontos_ausentes_na_inicializacao(self):
        parametros = Parametros(populacao=10, descendentes=10, geracoes=0, semente=10)
        inicial = executar(self.instancia, parametros)
        self.assertFalse(mesmos_pontos(inicial["pontos_nao_dominados"],
                                      enumerar(self.instancia)["pontos_nao_dominados"]))
        final = executar(self.instancia, replace(parametros, geracoes=40))
        self.assertTrue(mesmos_pontos(final["pontos_nao_dominados"],
                                     enumerar(self.instancia)["pontos_nao_dominados"]))

    def test_instancia_inviavel_nao_publica_fronteira_pareto_viavel(self):
        nos = tuple(replace(no, cpu=0.1) for no in self.instancia.nos)
        resultado = executar(replace(self.instancia, nos=nos), Parametros(
            populacao=8, descendentes=8, geracoes=3))
        self.assertEqual(resultado["fronteira"], [])
        self.assertEqual(resultado["individuos_viaveis_finais"], 0)
        self.assertGreater(resultado["menor_violacao_final"], 0)

    def test_zero_geracoes_avalia_apenas_populacao_inicial(self):
        resultado = executar(self.instancia, Parametros(populacao=4, geracoes=0))
        self.assertEqual(resultado["avaliacoes"], 4)
        self.assertEqual(len(resultado["historico"]), 1)

    def test_parametros_invalidos(self):
        for argumento in ({"populacao": 1}, {"descendentes": 0}, {"geracoes": -1},
                          {"prob_mutacao": 1.1}, {"prob_cruzamento": float("nan")},
                          {"eta": -1}, {"semente": 0.5}):
            with self.subTest(argumento=argumento), self.assertRaises(ValueError):
                Parametros(**argumento)

    def test_comparacao_de_pontos_independe_de_ordem_e_aceita_erro_numerico(self):
        self.assertTrue(mesmos_pontos([[0.5, 30.9], [0.75, 0]],
                                    [[0.75, 0], [0.5, 30.900000000000002]]))
        self.assertFalse(mesmos_pontos([[0.75, 0]], [[0.5, 30.9], [0.75, 0]]))
        self.assertFalse(mesmos_pontos([], [[0.75, 0]]))

    def test_validacao_nao_conta_sementes_repetidas_como_novas_execucoes(self):
        with self.assertRaises(ValueError):
            validar(self.instancia, Parametros(), [0, 0])


if __name__ == "__main__":
    unittest.main()
