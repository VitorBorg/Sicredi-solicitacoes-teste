import argparse
import json
import logging
from pathlib import Path

from iocontroller import IOController
from definitions import ARQUIVO_ENTRADA, ARQUIVO_LOG, ARQUIVO_SAIDA
from regras import selecionar


def argumentos_cli(argv=None):
    parser = argparse.ArgumentParser(
        description="Processa solicitações aprovadas e gera o CSV."
    )

    parser.add_argument(
        "--entrada",
        type=Path,
        default=ARQUIVO_ENTRADA,
        help="Arquivo JSON de entrada (padrão: %(default)s)",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=ARQUIVO_SAIDA,
        help="Arquivo CSV de saída (padrão: %(default)s)",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=ARQUIVO_LOG,
        help="Arquivo de log (padrão: %(default)s)",
    )

    return parser.parse_args(argv)


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


def executar(caminho_entrada, caminho_saida, arquivo_cls=IOController, selecao=selecionar):
    arquivo = arquivo_cls(caminho_entrada, caminho_saida)
    logging.info("Início do processamento")

    try:
        registros = arquivo.carregar()
    except FileNotFoundError:
        logging.error("Arquivo de entrada não encontrado: %s", caminho_entrada)
        return 1
    except json.JSONDecodeError as erro:
        logging.error("JSON inválido em %s: %s", caminho_entrada, erro)
        return 1
    except ValueError as erro:
        logging.error("Estrutura inesperada em %s: %s", caminho_entrada, erro)
        return 1

    logging.info("Total de registros lidos: %d", len(registros))

    aprovados, ignorados = selecao(registros)
    for registro, motivo in ignorados:
        logging.warning("Registro id=%s ignorado: %s", identificacao(registro), motivo)

    try:
        arquivo.exportar(aprovados)
    except OSError as erro:
        logging.error("Falha ao gerar %s: %s", caminho_saida, erro)
        return 1

    logging.info("Total de registros exportados: %d", len(aprovados))
    logging.info("Conclusão do processamento")

    return 0


def main():
    argumentos = argumentos_cli()
    configurar_log(argumentos.log)
    return executar(argumentos.entrada, argumentos.saida)


if __name__ == "__main__":
    raise SystemExit(main())
