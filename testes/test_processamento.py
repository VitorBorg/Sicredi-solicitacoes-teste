import tempfile
import unittest
from pathlib import Path

import main


class TesteMotivoParaIgnorar(unittest.TestCase):
    def test_aceita_registro_completo(self):
        registro = {"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"}
        self.assertIsNone(main.motivo_para_ignorar(registro))

    def test_ignora_cpf_vazio(self):
        registro = {"id": 2, "nome": "João Souza", "cpf": "", "status": "APROVADO"}
        self.assertEqual(main.motivo_para_ignorar(registro), "CPF nulo ou vazio")

    def test_ignora_cpf_nulo(self):
        registro = {"id": 2, "nome": "João Souza", "cpf": None, "status": "APROVADO"}
        self.assertEqual(main.motivo_para_ignorar(registro), "CPF nulo ou vazio")

    def test_ignora_status_diferente_de_aprovado(self):
        registro = {"id": 3, "nome": "Ana Oliveira", "cpf": "98765432100", "status": "PENDENTE"}
        self.assertIn("não é APROVADO", main.motivo_para_ignorar(registro))

    def test_ignora_cpf_com_formato_inesperado(self):
        registro = {"id": 4, "nome": "Pedro Santos", "cpf": "123", "status": "APROVADO"}
        self.assertIn("formato inesperado", main.motivo_para_ignorar(registro))

    def test_ignora_campos_obrigatorios_ausentes(self):
        registro = {"id": 5, "nome": "Juliana Costa", "status": "APROVADO"}
        self.assertIn("campos obrigatórios ausentes", main.motivo_para_ignorar(registro))

    def test_ignora_item_que_nao_e_objeto(self):
        self.assertIsNotNone(main.motivo_para_ignorar("texto solto"))


class TesteSelecionarParaExportacao(unittest.TestCase):
    def test_separa_aprovados_dos_ignorados(self):
        registros = [
            {"id": 1, "nome": "Maria Silva", "cpf": "12345678900", "status": "APROVADO"},
            {"id": 2, "nome": "João Souza", "cpf": "", "status": "APROVADO"},
            {"id": 3, "nome": "Ana Oliveira", "cpf": "98765432100", "status": "PENDENTE"},
        ]
        aprovados, ignorados = main.selecionar_para_exportacao(registros)

        self.assertEqual([registro["id"] for registro in aprovados], [1])
        self.assertEqual(len(ignorados), 2)


class TesteLeituraEescrita(unittest.TestCase):
    def test_le_arquivo_de_exemplo(self):
        registros = main.ler_solicitacoes(Path("solicitacoes.json"))
        self.assertEqual(len(registros), 15)

    def test_rejeita_json_cuja_raiz_nao_e_lista(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "entrada.json"
            caminho.write_text('{"id": 1}', encoding="utf-8")
            with self.assertRaises(ValueError):
                main.ler_solicitacoes(caminho)

    def test_escreve_csv_com_cabecalho_e_linhas(self):
        registros = [{"id": 1, "nome": "Maria Silva", "cpf": "12345678900"}]
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "aprovados.csv"
            main.escrever_csv(registros, caminho)
            linhas = caminho.read_text(encoding="utf-8").splitlines()

        self.assertEqual(linhas[0], "id;nome;cpf")
        self.assertEqual(linhas[1], "1;Maria Silva;12345678900")


if __name__ == "__main__":
    unittest.main()
