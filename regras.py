from pydantic import ValidationError

from definitions import Solicitacao, Status

def selecionar(registros):
    aprovados = []
    ignorados = []

    for registro in registros:
        solicitacao = None
        motivo = None

        if not isinstance(registro, dict):
            motivo = "item da lista não é um objeto JSON"
        else:
            try:
                solicitacao = Solicitacao.model_validate(registro)
            except ValidationError as erro:
                motivo = f"registro inválido: {_campos_com_erro(erro)}"
            else:
                motivo = motivo_para_ignorar(solicitacao)

        if motivo is None:
            aprovados.append(solicitacao)
        else:
            ignorados.append((registro, motivo))

    return aprovados, ignorados


def motivo_para_ignorar(solicitacao):
    if solicitacao.status is not Status.APROVADO:
        return f"status {solicitacao.status} não é válido para exportação."

    cpf = solicitacao.cpf.strip()
    if not cpf:
        return "CPF nulo ou vazio"

    return None


def _campos_com_erro(erro):
    return ", ".join(str(item["loc"][0]) for item in erro.errors())
