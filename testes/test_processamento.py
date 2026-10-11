import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from arquivo import ArquivoSolicitacoes
from definitions import Solicitacao
from regras import motivo_para_ignorar, selecionar


def montar_solicitacao(**campos):
    base = {"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"}
    base.update(campos)
    return Solicitacao.model_validate(base)


class TesteMotivoParaIgnorar(unittest.TestCase):
    def test_aceita_solicitacao_completa(self):
        self.assertIsNone(motivo_para_ignorar(montar_solicitacao()))

    def test_ignora_cpf_vazio(self):
        self.assertEqual(motivo_para_ignorar(montar_solicitacao(cpf="")), "CPF nulo ou vazio")

    def test_ignora_cpf_com_formato_inesperado(self):
        self.assertIn("formato inesperado", motivo_para_ignorar(montar_solicitacao(cpf="123")))

    def test_ignora_status_diferente_de_aprovado(self):
        self.assertIn("não é APROVADO", motivo_para_ignorar(montar_solicitacao(status="PENDENTE")))


class TesteSelecionar(unittest.TestCase):
    def test_separa_aprovados_dos_ignorados(self):
        registros = [
            {"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"},
            {"id": 2, "nome": "João Souza", "cpf": "", "status": "APROVADO"},
            {"id": 3, "nome": "Ana Oliveira", "cpf": "98765432100", "status": "PENDENTE"},
        ]
        aprovados, ignorados = selecionar(registros)

        self.assertEqual([solicitacao.id for solicitacao in aprovados], [1])
        self.assertEqual(len(ignorados), 2)

    def test_registro_sem_campo_obrigatorio_e_ignorado(self):
        aprovados, ignorados = selecionar([{"id": 1, "nome": "João Souza", "cpf": "12345678900"}])

        self.assertEqual(aprovados, [])
        self.assertIn("registro inválido", ignorados[0][1])

    def test_item_que_nao_e_objeto_e_ignorado(self):
        aprovados, ignorados = selecionar(["texto solto"])

        self.assertEqual(aprovados, [])
        self.assertIn("não é um objeto JSON", ignorados[0][1])


class TesteArquivoSolicitacoes(unittest.TestCase):
    def test_carrega_arquivo_de_exemplo(self):
        arquivo = ArquivoSolicitacoes(Path("solicitacoes.json"), Path("aprovados.csv"))
        self.assertEqual(len(arquivo.carregar()), 15)

    def test_rejeita_json_cuja_raiz_nao_e_lista(self):
        with tempfile.TemporaryDirectory() as pasta:
            entrada = Path(pasta) / "entrada.json"
            entrada.write_text('{"id": 1}', encoding="utf-8")
            arquivo = ArquivoSolicitacoes(entrada, Path(pasta) / "aprovados.csv")

            with self.assertRaises(ValueError):
                arquivo.carregar()

    def test_exporta_csv_com_cabecalho_e_linhas(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "aprovados.csv"
            ArquivoSolicitacoes(Path("solicitacoes.json"), saida).exportar([montar_solicitacao()])
            linhas = saida.read_text(encoding="utf-8").splitlines()

        self.assertEqual(linhas[0], "id;nome;cpf")
        self.assertEqual(linhas[1], "1;Maria Silva;12345678900")


class TesteFluxo(unittest.TestCase):
    def test_executar_gera_csv_com_os_aprovados(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            (pasta / "solicitacoes.json").write_text(
                '[{"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"}, '
                '{"id": 2, "nome": "João Souza", "cpf": "", "status": "APROVADO"}]',
                encoding="utf-8",
            )

            with patch("main.ARQUIVO_ENTRADA", pasta / "solicitacoes.json"), patch(
                "main.ARQUIVO_SAIDA", pasta / "aprovados.csv"
            ):
                codigo = main.executar()

            conteudo = (pasta / "aprovados.csv").read_text(encoding="utf-8")

        self.assertEqual(codigo, 0)
        self.assertIn("1;Maria Silva;12345678900", conteudo)
        self.assertNotIn("João Souza", conteudo)

    def test_executar_retorna_um_quando_o_arquivo_nao_existe(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)

            with patch("main.ARQUIVO_ENTRADA", pasta / "inexistente.json"), patch(
                "main.ARQUIVO_SAIDA", pasta / "aprovados.csv"
            ):
                codigo = main.executar()

        self.assertEqual(codigo, 1)

    def test_executar_retorna_um_com_json_invalido(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            (pasta / "solicitacoes.json").write_text("{invalido", encoding="utf-8")

            with patch("main.ARQUIVO_ENTRADA", pasta / "solicitacoes.json"), patch(
                "main.ARQUIVO_SAIDA", pasta / "aprovados.csv"
            ):
                codigo = main.executar()

        self.assertEqual(codigo, 1)


if __name__ == "__main__":
    unittest.main()
