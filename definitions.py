from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

class Status(StrEnum):
    APROVADO = "APROVADO"
    PENDENTE = "PENDENTE"
    REPROVADO = "REPROVADO"

class Solicitacao(BaseModel):
    id: int
    nome: str = Field(min_length=2, max_length=100)
    cpf: str
    status: Status

ARQUIVO_ENTRADA = Path("solicitacoes.json")
ARQUIVO_SAIDA = Path("aprovados.csv")
ARQUIVO_LOG = Path("processamento.log")

SEPARADOR_CSV = ";"
COLUNAS_CSV = ("id", "nome", "cpf")