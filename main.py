import csv
import json
import logging
from pathlib import Path

ARQUIVO_ENTRADA = Path("solicitacoes.json")
ARQUIVO_SAIDA = Path("aprovados.csv")
ARQUIVO_LOG = Path("processamento.log")

STATUS_APROVADO = "APROVADO"
CAMPOS_OBRIGATORIOS = ("id", "nome", "cpf", "status")


def configurar_log(caminho):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(caminho, mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def ler_solicitacoes(caminho):
    with caminho.open(encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    if not isinstance(dados, list):
        raise ValueError("o arquivo deveria conter uma lista de registros")

    return dados


def motivo_para_ignorar(registro):
    """Motivo pelo qual o registro não deve ser exportado, ou None se ele está apto."""
    if not isinstance(registro, dict):
        return "item da lista não é um objeto JSON"

    ausentes = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in registro]
    if ausentes:
        return "campos obrigatórios ausentes: " + ", ".join(ausentes)

    status = str(registro["status"]).strip().upper()
    if status != STATUS_APROVADO:
        return f"status {registro['status']!r} não é {STATUS_APROVADO}"

    cpf = registro["cpf"]
    if cpf is None or not str(cpf).strip():
        return "CPF nulo ou vazio"

    cpf = str(cpf).strip()
    if not cpf.isdigit() or len(cpf) != 11:
        return "CPF com formato inesperado (esperado 11 dígitos)"

    return None


def selecionar_para_exportacao(registros):
    """Separa os registros aptos dos ignorados, guardando o motivo de cada descarte."""
    aprovados = []
    ignorados = []

    for registro in registros:
        motivo = motivo_para_ignorar(registro)
        if motivo is None:
            aprovados.append(registro)
        else:
            ignorados.append((registro, motivo))

    return aprovados, ignorados


def identificacao(registro):
    if isinstance(registro, dict) and "id" in registro:
        return registro["id"]
    return "?"


def escrever_csv(aprovados, caminho):
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(["id", "nome", "cpf"])
        for registro in aprovados:
            escritor.writerow([registro["id"], registro["nome"], registro["cpf"]])


def main():
    configurar_log(ARQUIVO_LOG)
    logging.info("Início do processamento")

    try:
        registros = ler_solicitacoes(ARQUIVO_ENTRADA)
    except FileNotFoundError:
        logging.error("Arquivo de entrada não encontrado: %s", ARQUIVO_ENTRADA)
        return 1
    except json.JSONDecodeError as erro:
        logging.error("JSON inválido em %s: %s", ARQUIVO_ENTRADA, erro)
        return 1
    except ValueError as erro:
        logging.error("Estrutura inesperada em %s: %s", ARQUIVO_ENTRADA, erro)
        return 1

    logging.info("Total de registros lidos: %d", len(registros))

    aprovados, ignorados = selecionar_para_exportacao(registros)
    for registro, motivo in ignorados:
        logging.warning("Registro id=%s ignorado: %s", identificacao(registro), motivo)

    try:
        escrever_csv(aprovados, ARQUIVO_SAIDA)
    except OSError as erro:
        logging.error("Falha ao gerar %s: %s", ARQUIVO_SAIDA, erro)
        return 1

    logging.info("Total de registros exportados: %d", len(aprovados))
    logging.info("Conclusão do processamento")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
