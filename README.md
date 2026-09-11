# LLM Agent Monitor

Projeto desenvolvido para explorar integração entre aplicações Python e modelos de linguagem através de APIs REST.

## Sobre o projeto

A aplicação processa tarefas em JSON, chama um provider de IA, registra latência e logs e salva resultados estruturados. É um projeto de estudo voltado a aplicações de Inteligência Artificial e P&D, com um fluxo pequeno que pode ser acompanhado do início ao fim.

O agente é um executor de tarefas: recebe um prompt e consulta um cliente. Não realiza planejamento autônomo nem executa ferramentas.

## Funcionalidades

- Validação de entrada, IDs únicos e limpeza de texto.
- Providers mock local e OpenAI via HTTP.
- Timeout por requisição e retries com espera exponencial.
- Resultados de sucesso e erro com timestamp UTC e latência.
- Logs no console e em arquivo com rotação.
- CLI, health check e testes sem acesso à rede.

## Arquitetura

```text
JSON Input
    ↓
Data Processor
    ↓
Agent
    ↓
LLM Client
    ↓
OpenAI / Mock Provider
    ↓
Result Processor (save_results)
    ↓
JSON Output + Logs
```

`data_processor.py` valida todo o lote antes de qualquer chamada. `Agent` mede a execução e monta `TaskResult`. Os clientes retornam texto ou lançam `LLMError`; o agente transforma essa falha em um resultado de erro e continua as tarefas seguintes.

## Tecnologias

- Python 3.11 ou superior
- REST APIs e JSON
- OpenAI API e requests
- pytest e python-dotenv
- logging, pathlib, dataclasses e argparse
- Git e GitHub Actions

## Estrutura do projeto

```text
llm-agent-monitor/
├── src/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── data_processor.py
│   ├── llm_client.py
│   ├── health_check.py
│   ├── logger_config.py
│   └── models.py
├── tests/
├── data/
│   ├── input.example.json
│   └── output.example.json
├── logs/.gitkeep
├── .github/workflows/tests.yml
├── main.py
├── pytest.ini
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

## Como executar

Na pasta do projeto, com Python instalado:

```shell
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\activate
Copy-Item .env.example .env
```

Linux/macOS:

```bash
source .venv/bin/activate
cp .env.example .env
```

Instale as dependências e execute:

```shell
pip install -r requirements.txt
python main.py --input data/input.example.json --output data/output.json
```

`python main.py` usa os mesmos arquivos padrão. O `.env` é opcional no modo mock e sempre é procurado na raiz do projeto; variáveis já definidas no ambiente têm prioridade. Caminhos passados na CLI são relativos ao diretório atual.

O comando retorna código `0` em sucesso e `1` em falha de configuração, entrada, escrita ou de qualquer tarefa. Resultados são uma lista JSON e a saída existente é sobrescrita. Entrada e saída não podem ser o mesmo caminho. O lote é salvo ao final; uma interrupção antes disso não cria checkpoint.

## Modo Mock

Nenhuma chave externa é necessária. Sem `.env`, o padrão também é mock.

```dotenv
LLM_PROVIDER=mock
```

As respostas são determinísticas, com prefixo `[MOCK]` seguido do prompt. Servem para verificar o fluxo, não para simular a qualidade de um modelo real.

## OpenAI

No `.env`, configure:

```dotenv
LLM_PROVIDER=openai
OPENAI_API_KEY=sua-chave-aqui
OPENAI_MODEL=modelo-disponivel-na-sua-conta
MAX_RETRIES=3
REQUEST_TIMEOUT=30
```

Substitua os valores ilustrativos por uma chave e um modelo habilitado na sua conta. O modelo é obrigatório nesse modo, evitando uma escolha de custo ou disponibilidade implícita. Configuração incompleta produz erro; não há troca silenciosa para mock.

A integração usa `POST https://api.openai.com/v1/responses`, envia `model`, `input` e `store: false` e extrai os blocos `output_text` de mensagens concluídas, conforme a [documentação oficial da Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create). O uso real depende de acesso e saldo na conta e pode gerar cobrança.

`MAX_RETRIES` é o número de tentativas adicionais (0 a 10). Com 3, são até 4 chamadas. Timeout/conexão, HTTP 408, 409, 429 e 5xx permitem retry, com esperas de 1, 2, 4 segundos, limitadas a 30 segundos. Outros erros HTTP e respostas inválidas não são repetidos. A política é simples e não interpreta `Retry-After`. Repetir após timeout pode gerar outra chamada cobrada.

`REQUEST_TIMEOUT` deve ser positivo e finito, em segundos; controla o timeout de conexão/leitura do requests, não um prazo total do lote. `latency_ms` mede o tempo total do cliente, incluindo retries e esperas.

Chaves, prompts e corpos de resposta da API não são escritos nos logs. A saída JSON contém a resposta do modelo e deve ser tratada conforme os dados enviados. `.env`, logs e `data/output.json` são ignorados pelo Git; arquivos de saída com outros nomes precisam ser revisados antes de publicar.

## Health Check

```shell
python -m src.health_check
```

Imprime um objeto JSON em stdout, com `provider`, `status`, `latency_ms` e `timestamp`; falhas incluem `error`. Logs vão para stderr e `logs/app.log`. Retorna `0` para `healthy` e `1` para `unavailable`.

No modo OpenAI, faz uma geração curta real e pode gerar cobrança. No modo mock, funciona totalmente offline.

## Testes

```shell
pytest
```

Ou `python -m pytest`. A suíte bloqueia HTTP real e simula respostas e falhas. Cobre normalização, entradas inválidas, IDs duplicados, salvamento, agente, contrato HTTP, retries, configuração, CLI e health check. A integração com uma conta real não é validada por esses testes. O workflow executa a suíte e os comandos mock no GitHub Actions.

## Exemplo de entrada

```json
[
  {"id": "task-001", "prompt": "O que é uma API REST?"}
]
```

A lista deve ser não vazia. `id` e `prompt` são textos obrigatórios; IDs aceitam letras, números, `_`, `.` e `-`, diferenciam maiúsculas de minúsculas e são comparados após remoção de espaços nas extremidades. Campos adicionais são ignorados. A limpeza remove espaços nas extremidades e no fim das linhas e padroniza quebras de linha, preservando espaços internos e indentação de código.

## Exemplo de saída

```json
[
  {
    "task_id": "task-001",
    "provider": "mock",
    "status": "success",
    "latency_ms": 0.012,
    "response": "[MOCK] Resposta simulada para: O que é uma API REST?",
    "timestamp": "2026-09-11T12:00:00+00:00",
    "error": null
  }
]
```

Valores de tempo são ilustrativos. Em falha, `status` é `error`, `response` é `null` e `error` contém a mensagem. O arquivo `data/output.example.json` traz uma execução mock completa.

## Conceitos praticados

- Consumo de APIs REST e manipulação de JSON.
- Integração com modelos de linguagem.
- Tratamento de erros, retry e logging.
- Preparação e validação de dados.
- Testes automatizados com mocks.
- Configuração através de environment variables.
- Separação de responsabilidades e versionamento com Git.

## Próximos passos

- Suporte a outros providers.
- Métricas agregadas por execução.
- Armazenamento em banco de dados.
- Dashboard simples.
- Execução assíncrona com limite de concorrência.
- Observabilidade com métricas e traces.

## Licença

MIT. Consulte [LICENSE](LICENSE).
