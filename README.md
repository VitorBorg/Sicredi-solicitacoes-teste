# Sistema para automação da validação de solicitações de cadastro

O sistema recebe solicitações, as verifica, e todas que estiverem válidas são salvas em um novo arquivo.

## Detalhamento

1. Via CLI a solução recebe um arquivo .json, se não for explicitado no comando CLI, busca na raiz é solicitacoes.json.
2. aplica as regras de negócio.
Isso implica em verificação de campos obrigatórios vazios (cpf), verificação de valores de campos (o enum status precisa ser APROVADO), verificações de tipo (como o cpf não contendo apenas dígitos numéricos), regras específicas dos campos (cpf como string, status como enum, cpf nao vazio/null, etc...), e também má formatação do json.
3. escreve os registros válidos em um arquivo chamado aprovados.csv (se não for explicitado no comando CLI), e gera um arquivo de logs para observabilidade chamado processamento.log.

## Pré-requisitos

Python 3.11 ou superior, por causa do `enum.StrEnum`. A única dependência é o `pydantic` (v2), usada no modelo de validação.

    pip install -r requirements.txt

## Como executar

Na raiz do projeto, o comando usa por padrão as constantes de `definitions.py`:

    python main.py

Os caminhos podem ser ajustados pela linha de comando:

    python main.py --entrada solicitacoes.json --saida aprovados.csv --log processamento.log

Sem o flag, cada opção volta para a constante correspondente (`--entrada`, `--saida` e `--log`).

Ao final são gerados `aprovados.csv` e `processamento.log`. O código de saída é 0 em caso de sucesso e 1 quando um erro impede o processamento: arquivo de entrada ausente, JSON inválido, raiz que não é uma lista ou falha ao escrever o CSV.

## Como rodar os testes

    python -m unittest

## Resultado com o arquivo de exemplo

O `solicitacoes.json` fornecido tem 15 registros. São exportados 7 e ignorados 8: 4 com status `PENDENTE`, 2 com `REPROVADO` e 2 aprovados com CPF vazio.

# Implementação

## Premissas e decisões

Como o documento explicíta que não busca soluções complexas, concluí que a prioridade gira em torno de uma solução de alta manutenibilidade, testabilidade e observabilidade. Para isso, tomei cuidado em diminuir o encapsulamento, isolando as regras de negócio do processamento (I/O), mas sem aumentar muito a granularidade desse encapsulamento.

Dessa forma, defini 5 separações principais:
* main.py: é o orquestrador.
* definitions.py: contém as classes, enums e constantes.
* regras.py: a aplicação das regras de negócio.
* iocontroller.py: responsável pelo I/O.
* testes: Se subdividem em 4 arquivos que é um divisão de responsabilidades. Mas são os testes de unidade do sistema. (mais detalhes abaixo).


1. O separador csv usado foi ";". Já alinhado com a sugestão feita no próprio documento do teste, parece uma escolha segura considerando a compatibilidade em português do excel pois usa como seprador de lista, então o arquivo abre certo com um duplo clique, sem passar pela importação de dados.
2. A codificação é UTF-8 sem BOM, como indicado no documento.
3. Utilização do pydantic (que é uma biblioteca para validação e modelagem de dados) para criação do model das solicitações. Auxiliando na garantia de tipagem (id sempre um número, cpf tratado como string para evitar perda de '0's na frente), validação de conteúdo no campo nome e no campo status.
4. criação de um arquivo definitions que mantém constantes e definições de enum e classe, para facilitar a leitura e manutenção dessas definições. Visto que o escopo da solução é pequeno, achei mais adequado manter apenas um arquivo. Não acredito que a separação se torna justificável.
5. o log sai pelo módulo logging (na escrita no arquivo processamento.log e no console).
6. Os testes foram separados por responsabilidades:
* test_regras.py: o escopo são as regras de negócio
* test_io.py: o escopo é a leitura do json e a escrita do csv.
* test_cli: o escopo são os comandos via terminal
* test_main.py: escopo é basicamente a orquestração 

No total são 20 testes: 7 de regras, 3 de I/O, 8 do orquestrador e apenas 2 do CLI.

## Uso de ferramentas

Utilizei ferramentas de IA para validação da estrutura que havia pensado para o projeto (sempre mantendo bastante cuidado com overengineering), melhorias e otimizações para o código.
Para isso utilizei a ferramenta open source Cline, integrado ao visual studio code, com o modelo Deepseek 4.1 flash. Além de usar algumas ias em versão web como consultas rápidas (gpt e gemini).

## Resposta

Pergunta:
"Como você adaptaria essa solução para um processo de BPM, no qual os registros fossem
recebidos por um formulário e o arquivo CSV fosse gerado após uma etapa de
aprovação?"

A lógica de processamento da solução desenvolvida poderia ser reaproveitada, mas para se adaptar precisaríamos olhar para o processo e entender como a comunicação entre as etapas está sendo feita, para então integrar a solução dentro do processo.
Portanto, neste fluxo hipotético, o formulário passa a ser o ponto de partida, que aciona o processo BPM. Após a etapa de aprovação, a solução seria acionada para receber os registros e como saída o arquivo csv (e o log também). A integração dessas saídas dentro do BPM fica a cargo de entender as particularides do processo para poder implementar de maneira coerente.
