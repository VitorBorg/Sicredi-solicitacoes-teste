import tempfile
import unittest
from pathlib import Path

import main
from regras import selecionar


class TesteFluxo(unittest.TestCase):
    def test_executar_gera_csv_com_os_aprovados(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            (pasta / "solicitacoes.json").write_text(
                '[{"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"}, '
                '{"id": 2, "nome": "João Souza", "cpf": "", "status": "APROVADO"}]',
                encoding="utf-8",
            )

            codigo = main.executar(pasta / "solicitacoes.json", pasta / "aprovados.csv")
            conteudo = (pasta / "aprovados.csv").read_text(encoding="utf-8")

        self.assertEqual(codigo, 0)
        self.assertIn("1;Maria Silva;12345678900", conteudo)
        self.assertNotIn("João Souza", conteudo)

    def test_executar_retorna_um_quando_o_arquivo_nao_existe(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            codigo = main.executar(pasta / "inexistente.json", pasta / "aprovados.csv")

        self.assertEqual(codigo, 1)

    def test_executar_retorna_um_com_json_invalido(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            (pasta / "solicitacoes.json").write_text("{invalido", encoding="utf-8")
            codigo = main.executar(pasta / "solicitacoes.json", pasta / "aprovados.csv")

        self.assertEqual(codigo, 1)

    def test_executar_retorna_um_quando_a_entrada_nao_pode_ser_lida(self):
        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            diretorio = pasta / "pasta"
            diretorio.mkdir()
            codigo = main.executar(diretorio, pasta / "aprovados.csv")

        self.assertEqual(codigo, 1)


class TesteArgumentosCLI(unittest.TestCase):
    def test_sem_argumentos_usa_as_constantes(self):
        argumentos = main.argumentos_cli([])

        self.assertEqual(argumentos.entrada, main.ARQUIVO_ENTRADA)
        self.assertEqual(argumentos.saida, main.ARQUIVO_SAIDA)
        self.assertEqual(argumentos.log, main.ARQUIVO_LOG)

    def test_aceita_caminhos_pelos_flags(self):
        argumentos = main.argumentos_cli(
            ["--entrada", "outro.json", "--saida", "outro.csv", "--log", "outro.log"]
        )

        self.assertEqual(argumentos.entrada, Path("outro.json"))
        self.assertEqual(argumentos.saida, Path("outro.csv"))
        self.assertEqual(argumentos.log, Path("outro.log"))


class ArquivoFake:
    def __init__(self, entrada=None, saida=None):
        self.entrada = entrada
        self.saida = saida
        self.registros = []
        self.exportados = None

    def carregar(self):
        return self.registros

    def exportar(self, aprovados):
        self.exportados = aprovados


class TesteExecutarComDependenciasInjetadas(unittest.TestCase):
    def test_executar_usa_as_dependencias_injetadas_sem_disco(self):
        arquivo = ArquivoFake()
        arquivo.registros = [
            {"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"},
            {"id": 2, "nome": "João Souza", "cpf": "", "status": "APROVADO"},
        ]

        codigo = main.executar(
            "entrada.json",
            "aprovados.csv",
            arquivo_cls=lambda entrada, saida: arquivo,
            selecao=selecionar,
        )

        self.assertEqual(codigo, 0)
        self.assertEqual([solicitacao.id for solicitacao in arquivo.exportados], [1])

    def test_executar_chama_a_funcao_de_selecao_injetada(self):
        arquivo = ArquivoFake()
        arquivo.registros = [
            {"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"}
        ]

        def selecao_fake(_):
            return [], []

        codigo = main.executar(
            "entrada.json",
            "aprovados.csv",
            arquivo_cls=lambda entrada, saida: arquivo,
            selecao=selecao_fake,
        )

        self.assertEqual(codigo, 0)
        self.assertEqual(arquivo.exportados, [])


if __name__ == "__main__":
    unittest.main()

