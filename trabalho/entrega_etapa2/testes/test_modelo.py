"""Contas manuais e fronteira conhecida para validar o modelo antes do MOMA."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from codigo.exato import enumerar
from codigo.modelo import Instancia, Interacao, No, Servico, avaliar, carregar_instancia, domina


DADOS = Path(__file__).resolve().parent.parent / "dados" / "pequena.json"


class TestModelo(unittest.TestCase):
    def setUp(self):
        self.instancia = carregar_instancia(DADOS)

    def test_colocacao(self):
        resultado = avaliar(self.instancia, [[1, 0], [1, 0]])
        self.assertTrue(resultado.viavel)
        self.assertEqual(resultado.cpu_usada, (3, 0))
        self.assertEqual(resultado.memoria_usada, (6, 0))
        self.assertEqual(resultado.objetivos, (0.75, 0))

    def test_divisao_equilibrada(self):
        resultado = avaliar(self.instancia, [[0, 1], [1, 0]])
        self.assertTrue(resultado.viavel)
        self.assertEqual(resultado.balanceamento, 0.5)
        self.assertAlmostEqual(resultado.comunicacao, 30.9)
        self.assertEqual(resultado.sigma_cluster, 0)

    def test_duas_replicas_no_mesmo_no(self):
        resultado = avaliar(self.instancia, [[2, 0], [0, 1]])
        self.assertEqual(resultado.cpu_usada, (2, 2))
        self.assertAlmostEqual(resultado.comunicacao, 30.3)
        self.assertTrue(resultado.viavel)

    def test_trafego_dividido_entre_replicas(self):
        resultado = avaliar(self.instancia, [[1, 1], [1, 0]])
        self.assertAlmostEqual(resultado.comunicacao, 15.45)
        self.assertEqual(resultado.balanceamento, 0.75)

    def test_excesso_de_capacidade(self):
        resultado = avaliar(self.instancia, [[0, 1], [0, 1]])
        self.assertFalse(resultado.viavel)
        # CPU: 3/2 - 1 = 0,5; memória: 6/4 - 1 = 0,5.
        self.assertEqual(resultado.violacao, 1)

    def test_ausencia_e_excesso_de_replicas(self):
        ausente = avaliar(self.instancia, [[0, 0], [1, 0]])
        excesso = avaliar(self.instancia, [[3, 0], [0, 1]])
        self.assertEqual(ausente.violacao, 1)
        self.assertEqual(excesso.violacao, 0.5)
        self.assertFalse(ausente.viavel)

    def test_pesos_quando_desvios_sao_diferentes(self):
        instancia = Instancia(
            "pesos", (No("a", "c1", 4, 8, 0), No("b", "c1", 2, 4, 0)),
            (Servico("s0", 1, 1, 1, 1), Servico("s1", 2, 1, 1, 1)),
            ((0, 3), (3, 0)), (Interacao(0, 1, 10),))
        resultado = avaliar(instancia, [[1, 0], [0, 1]])
        # sigma_cpu = 0,375; sigma_mem = 0,0625 => pesos 6/7 e 1/7.
        self.assertAlmostEqual(resultado.balanceamento, 25 / 28)
        self.assertAlmostEqual(resultado.sigma_cluster, (0.375**2 + 0.0625**2)**0.5 / 2)

    def test_zero_desvio_com_carga_nao_nula(self):
        nos = tuple(replace(no, cluster="unico") for no in self.instancia.nos)
        resultado = avaliar(replace(self.instancia, nos=nos), [[0, 1], [1, 0]])
        self.assertEqual(resultado.balanceamento, 0.5)

    def test_dominancia_preserva_compromissos(self):
        colocada = avaliar(self.instancia, [[1, 0], [1, 0]])
        equilibrada = avaliar(self.instancia, [[0, 1], [1, 0]])
        pior = avaliar(self.instancia, [[1, 1], [1, 0]])
        inviavel = avaliar(self.instancia, [[0, 0], [1, 0]])
        self.assertFalse(domina(colocada, equilibrada))
        self.assertFalse(domina(equilibrada, colocada))
        self.assertTrue(domina(colocada, pior))
        self.assertTrue(domina(colocada, inviavel))
        self.assertFalse(domina(colocada, colocada))

    def test_formato_da_alocacao(self):
        for alocacao in ([[1, 0]], [[1], [1]], [[-1, 0], [1, 0]],
                         [[1.5, 0], [1, 0]], [[True, 0], [1, 0]]):
            with self.subTest(alocacao=alocacao), self.assertRaises(ValueError):
                avaliar(self.instancia, alocacao)

    def test_instancia_invalida(self):
        original = json.loads(DADOS.read_text(encoding="utf-8"))
        for campo, valor in (("nos", []), ("distancias", [[1, 3], [3, 0]]),
                             ("distancias", [[0, float("nan")], [3, 0]]),
                             ("servicos", []), ("modelo", "outro")):
            with self.subTest(campo=campo, valor=valor), tempfile.TemporaryDirectory() as pasta:
                dados = {**original, campo: valor}
                caminho = Path(pasta) / "instancia.json"
                caminho.write_text(json.dumps(dados), encoding="utf-8")
                with self.assertRaises(ValueError):
                    carregar_instancia(caminho)

    def test_fronteira_exata_conhecida(self):
        resultado = enumerar(self.instancia)
        # Cada serviço tem 2 distribuições de uma réplica e 3 de duas: 5 * 5.
        self.assertEqual(resultado["solucoes_enumeradas"], 25)
        self.assertEqual(resultado["solucoes_viaveis"], 11)
        pontos = resultado["pontos_nao_dominados"]
        self.assertEqual(len(pontos), 2)
        self.assertAlmostEqual(pontos[0][0], 0.5)
        self.assertAlmostEqual(pontos[0][1], 30.9)
        self.assertEqual(pontos[1], [0.75, 0])

    def test_limite_de_enumeracao(self):
        with self.assertRaises(ValueError):
            enumerar(self.instancia, limite=24)


if __name__ == "__main__":
    unittest.main()
