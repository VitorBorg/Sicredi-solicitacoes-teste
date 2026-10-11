import json
import logging

from arquivo import ArquivoSolicitacoes
from definitions import ARQUIVO_ENTRADA, ARQUIVO_LOG, ARQUIVO_SAIDA
from regras import selecionar


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


def identificacao(registro):
    if isinstance(registro, dict) and "id" in registro:
        return registro["id"]
    return "?"


def executar():
    arquivo = ArquivoSolicitacoes(ARQUIVO_ENTRADA, ARQUIVO_SAIDA)
    logging.info("Início do processamento")

    try:
        registros = arquivo.carregar()
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

    aprovados, ignorados = selecionar(registros)
    for registro, motivo in ignorados:
        logging.warning("Registro id=%s ignorado: %s", identificacao(registro), motivo)

    try:
        arquivo.exportar(aprovados)
    except OSError as erro:
        logging.error("Falha ao gerar %s: %s", ARQUIVO_SAIDA, erro)
        return 1

    logging.info("Total de registros exportados: %d", len(aprovados))
    logging.info("Conclusão do processamento")

    return 0


def main():
    configurar_log(ARQUIVO_LOG)
    return executar()


if __name__ == "__main__":
    raise SystemExit(main())
