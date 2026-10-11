import unittest

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


if __name__ == "__main__":
    unittest.main()

