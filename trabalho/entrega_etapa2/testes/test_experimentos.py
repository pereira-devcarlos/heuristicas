"""Verifica hipervolume, geração de dados e orçamento dos comparadores."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codigo.comparadores import METODOS, executar_comparador
from codigo.experimentos import rodar
from codigo.gerar_instancias import gerar
from codigo.metricas import escala_comunicacao, hipervolume, medir
from codigo.modelo import avaliar, carregar_instancia, domina
from codigo.moma import Parametros


RAIZ = Path(__file__).resolve().parent.parent


class TestExperimentos(unittest.TestCase):
    def setUp(self):
        self.instancia = carregar_instancia(RAIZ / "dados" / "pequena.json")

    def test_hipervolume_union_de_retangulos(self):
        self.assertEqual(hipervolume([[1, 4], [1.5, 2]], (2, 5)), 2)
        self.assertEqual(hipervolume([[1.5, 2], [1, 4], [1, 4], [1.8, 4.5]], (2, 5)), 2)
        self.assertEqual(hipervolume([], (2, 5)), 0)

    def test_referencia_invalida_nao_e_recortada_silenciosamente(self):
        for pontos in ([[1.1, 0]], [[0, float("nan")]], [[0, 0, 0]]):
            with self.subTest(pontos=pontos), self.assertRaises(ValueError):
                hipervolume(pontos)

    def test_normalizacao_independente_do_metodo(self):
        escala = escala_comunicacao(self.instancia)
        self.assertAlmostEqual(escala, 10 * 3 * 1.03)
        a = medir(self.instancia, [[0.75, 0]])
        b = medir(self.instancia, [[0.5, 30.9]])
        self.assertEqual(a["escala_comunicacao"], b["escala_comunicacao"])
        self.assertAlmostEqual(a["hipervolume"], (1.1 - 0.75) * 1.1)

    def test_comparadores_contam_todas_as_chamadas_ao_avaliador(self):
        for metodo in METODOS:
            with self.subTest(metodo=metodo):
                with patch("codigo.comparadores.avaliar", wraps=avaliar) as contador:
                    resultado = executar_comparador(self.instancia, metodo, 53, 0)
                    self.assertEqual(contador.call_count, 53)
                self.assertEqual(resultado["avaliacoes"], 53)
                avaliacoes = []
                for ponto in resultado["fronteira"]:
                    av = avaliar(self.instancia, ponto["alocacao"])
                    self.assertTrue(av.viavel)
                    self.assertEqual(list(av.objetivos), ponto["objetivos"])
                    avaliacoes.append(av)
                self.assertFalse(any(domina(a, b) for a in avaliacoes for b in avaliacoes))

    def test_orcamento_menor_que_uma_construcao(self):
        for metodo in METODOS[1:]:
            resultado = executar_comparador(self.instancia, metodo, 1, 0)
            self.assertEqual(resultado["avaliacoes"], 1)
            self.assertEqual(resultado["fronteira"], [])

    def test_comparadores_reproduziveis(self):
        for metodo in METODOS:
            a = executar_comparador(self.instancia, metodo, 30, 2)
            b = executar_comparador(self.instancia, metodo, 30, 2)
            a.pop("tempo_segundos")
            b.pop("tempo_segundos")
            self.assertEqual(a, b)

    def test_geracao_deterministica_com_seis_instancias_viaveis(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminhos_a = gerar(Path(pasta) / "a")
            caminhos_b = gerar(Path(pasta) / "b")
            self.assertEqual(len(caminhos_a), 6)
            for a, b in zip(caminhos_a, caminhos_b):
                self.assertEqual(a.read_bytes(), b.read_bytes())
                instancia = carregar_instancia(a)
                self.assertEqual(len(instancia.nos), 6)
                self.assertEqual(len({n.cluster for n in instancia.nos}), 3)
                testemunha = [[1, 0, 0, 0, 0, 0] for _ in instancia.servicos]
                self.assertTrue(avaliar(instancia, testemunha).viavel)

    def test_transcricao_edgex_consistente_com_recorte_anterior(self):
        dados = json.loads((RAIZ / "dados" / "recursos_artigo.json").read_text())
        recorte = json.loads((RAIZ / "dados" / "edgex_1_usuario_recursos.json").read_text())
        aplicacao = dados["aplicacoes"]["edgex"]
        self.assertEqual(aplicacao["ids"], [s["id"] for s in recorte["servicos"]])
        self.assertEqual(aplicacao["1"], [[s["cpu"], s["memoria"]] for s in recorte["servicos"]])

    def test_pipeline_salva_resultados_e_preserva_diretorio_existente(self):
        with tempfile.TemporaryDirectory() as pasta, contextlib.redirect_stdout(io.StringIO()):
            destino = Path(pasta)
            parametros = Parametros(populacao=4, descendentes=4, geracoes=1)
            rodar([RAIZ / "dados" / "pequena.json"], destino, parametros, [0])
            self.assertEqual(len(list((destino / "execucoes").rglob("*.json"))), 4)
            self.assertTrue((destino / "analise.md").exists())
            self.assertTrue((destino / "execucoes.csv").exists())
            with self.assertRaises(ValueError):
                rodar([RAIZ / "dados" / "pequena.json"], destino, parametros, [0])


if __name__ == "__main__":
    unittest.main()
