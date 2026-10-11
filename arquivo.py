import csv
import json

from definitions import COLUNAS_CSV, SEPARADOR_CSV


class ArquivoSolicitacoes:
    def __init__(self, entrada, saida):
        self.entrada = entrada
        self.saida = saida

    def carregar(self):
        with self.entrada.open(encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        if not isinstance(dados, list):
            raise ValueError("o arquivo deveria conter uma lista de registros")

        return dados

    def exportar(self, aprovados):
        with self.saida.open("w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.writer(arquivo, delimiter=SEPARADOR_CSV)
            escritor.writerow(COLUNAS_CSV)
            for solicitacao in aprovados:
                escritor.writerow([getattr(solicitacao, coluna) for coluna in COLUNAS_CSV])
