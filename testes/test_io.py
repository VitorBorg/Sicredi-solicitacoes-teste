import tempfile
import unittest
from pathlib import Path

from definitions import Solicitacao
from iocontroller import IOController


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
            solicitacao = Solicitacao(
                id=1, nome="Maria Silva", cpf="12345678900", status="APROVADO"
            )
            IOController(Path("solicitacoes.json"), saida).exportar([solicitacao])
            linhas = saida.read_text(encoding="utf-8").splitlines()

        self.assertEqual(linhas[0], "id;nome;cpf")
        self.assertEqual(linhas[1], "1;Maria Silva;12345678900")


if __name__ == "__main__":
    unittest.main()

