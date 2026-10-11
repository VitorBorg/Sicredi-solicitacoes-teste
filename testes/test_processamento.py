import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import main
from iocontroller import IOController
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

    def test_ignora_registro_com_cpf_nulo(self):
        aprovados, ignorados = selecionar(
            [{"id": 1, "nome": "Maria Silva", "cpf": None, "status": "APROVADO"}]
        )

        self.assertEqual(aprovados, [])
        self.assertEqual(ignorados[0][1], "registro inválido: cpf")


class TesteIOController(unittest.TestCase):
    def test_carrega_arquivo_de_exemplo(self):
        arquivo = IOController(Path("solicitacoes.json"), Path("aprovados.csv"))
        self.assertEqual(len(arquivo.carregar()), 15)

    def test_rejeita_json_cuja_raiz_nao_e_lista(self):
        with tempfile.TemporaryDirectory() as pasta:
            entrada = Path(pasta) / "entrada.json"
            entrada.write_text('{"id": 1}', encoding="utf-8")
            arquivo = IOController(entrada, Path(pasta) / "aprovados.csv")

            with self.assertRaises(ValueError):
                arquivo.carregar()

    def test_exporta_csv_com_cabecalho_e_linhas(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta) / "aprovados.csv"
            IOController(Path("solicitacoes.json"), saida).exportar([montar_solicitacao()])
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


class TesteCLIFimAFim(unittest.TestCase):
    def test_main_processa_a_entrada_pela_linha_de_comando(self):
        raiz = Path(__file__).resolve().parent.parent

        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            entrada = pasta / "solicitacoes.json"
            saida = pasta / "aprovados.csv"
            log = pasta / "processamento.log"
            entrada.write_text(
                '[{"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"}, '
                '{"id": 3, "nome": "Ana Oliveira", "cpf": "98765432100", "status": "PENDENTE"}]',
                encoding="utf-8",
            )

            resultado = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--entrada", str(entrada),
                    "--saida", str(saida),
                    "--log", str(log),
                ],
                cwd=raiz,
                capture_output=True,
                text=True,
            )

            conteudo = saida.read_text(encoding="utf-8")

        self.assertEqual(resultado.returncode, 0)
        self.assertEqual(conteudo.splitlines()[0], "id;nome;cpf")
        self.assertIn("1;Maria Silva;12345678900", conteudo)
        self.assertNotIn("Ana Oliveira", conteudo)

    def test_main_retorna_erro_na_cli_quando_arquivo_nao_existe(self):
        raiz = Path(__file__).resolve().parent.parent

        with tempfile.TemporaryDirectory() as pasta:
            resultado = subprocess.run(
                [
                    sys.executable,
                    "main.py",
                    "--entrada", str(Path(pasta) / "inexistente.json"),
                    "--saida", str(Path(pasta) / "aprovados.csv"),
                    "--log", str(Path(pasta) / "processamento.log"),
                ],
                cwd=raiz,
                capture_output=True,
                text=True,
            )

        self.assertEqual(resultado.returncode, 1)


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
