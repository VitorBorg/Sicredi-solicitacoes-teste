import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()

