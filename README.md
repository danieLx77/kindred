# Kindred

Aplicação web para descoberta de projetos sociais. O repositório contém um frontend React + TypeScript + Vite e uma API inicial em Python + FastAPI.

## Pré-requisitos

- Node.js 26.11.1 e npm;
- Para o backend: Python 3.10 ou superior e [uv](https://docs.astral.sh/uv/getting-started/installation/), ou Docker com BuildKit/Buildx.

## Frontend

Instale as dependências e inicie o servidor de desenvolvimento:

```bash
cd frontend
npm ci
npm run dev
```

Para gerar o build de produção, executar as verificações de qualidade e conferir a formatação:

```bash
npm run build
npm run lint
npm run format:check
```

Para aplicar a formatação, use `npm run format`.

Para executar os testes em modo interativo, validar a suíte uma vez ou consultar a cobertura V8:

```bash
npm test
npm run test:run
npm run test:coverage
```

O lint executa Oxlint seguido de ESLint; o Oxlint cobre rapidamente as regras suportadas e o ESLint complementa a análise com regras e plugins adicionais. O Oxfmt formata os arquivos. São ferramentas recentes, adotadas para manter verificações locais rápidas sem perder cobertura necessária. Usuários do VS Code também recebem recomendações opcionais de extensão em `.vscode/extensions.json`.

## Backend

Sincronize o ambiente com as versões registradas em `uv.lock`:

```bash
cd backend
uv sync --locked
```

Execute a API localmente (os comandos abaixo partem de `backend/`):

```bash
uv run --locked uvicorn main:app --reload
```

Verifique lint, formatação e tipos:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pyright
```

Para aplicar correções automáticas seguras de lint ou formatar o código, quando necessário:

```bash
uv run --locked ruff check --fix .
uv run --locked ruff format .
```

### Descoberta GlobalGiving (issue #12)

`integrations.globalgiving.GlobalGivingDiscoveryAdapter` implementa a operação
`discover` do contrato de projetos da #10. A consulta de detalhe (`get_project`)
permanece na #13; este componente ainda não é o `ProjectProvider` completo.
Não há novas rotas públicas. Use uma instância por ciclo de vida da aplicação,
com `async with` ou fechamento explícito por `aclose()`.

A chave vem exclusivamente de `GLOBALGIVING_API_KEY` no ambiente do backend;
o adapter não lê `.env` automaticamente. A URL base padrão é HTTPS, o timeout
total e por fase é 10 segundos, a resposta é limitada a 2 MiB e não há retries
nem redirecionamentos automáticos. HTTPX agora é dependência de execução.
Logs HTTPX/HTTPcore são suprimidos apenas no contexto dessas chamadas, inclusive
leitura e fechamento, para não registrar a chave exigida na query string. O
cliente próprio não instala hooks de tracing nem usa proxies do ambiente.

Cada chamada busca no máximo um lote externo de 10 itens. `page_size` é um
limite superior; lotes podem ser menores. Na listagem, lotes menores são retomados
com a mesma posição externa e um deslocamento interno, sem cache de projetos.
Na busca, qualquer lote não vazio permite tentar a próxima posição; apenas uma
resposta vazia confirma o fim, independentemente de `numberFound`. Isso pode
exigir uma chamada adicional no final. Não há garantia de snapshot estável.

As continuações são estado interno assinado, vinculado à consulta e à instância,
sem armazenamento de páginas. Permitem replay enquanto a instância existir;
reinício ou outra instância invalida o handle. A assinatura impede adulteração,
mas não é criptografia: esses tokens internos não devem ser publicados diretamente
pela futura API #15. Filtros de tema/país ainda são rejeitados explicitamente.

A #10 deixou categorias de falhas para a integração. A decisão nesta entrega é
usar `projects.errors.ProviderError` com `ProviderFailure`: entrada inválida,
autenticação, recurso ausente, indisponibilidade, limite de taxa, timeout, rede
ou resposta inválida. Não carrega URL, corpo ou exceção bruta. Um 404 de descoberta
é falha da operação, não uma lista vazia. A tradução em HTTP público fica na #15.
Campos opcionais inválidos são omitidos; ID de projeto inválido rejeita o lote.
Organização sem ID utilizável não gera referência fictícia.

Os testes de integração usam RESPX com requisições não previstas bloqueadas,
transportes locais e uma chave fictícia. Não exigem acesso real à GlobalGiving.

Execute a suíte e gere um relatório de cobertura sem limite mínimo:

```bash
uv run --locked python -m pytest
uv run --locked python -m pytest --cov=main --cov-report=term-missing
```

Para desenvolver o backend sem instalar Python e uv no host, use o ambiente Docker descrito no [workflow de contribuição](docs/contributing/workflow.md#backend-com-docker).
