# Kindred

Aplicação web para descoberta de projetos sociais. O repositório contém um frontend React + TypeScript + Vite e uma API inicial em Python + FastAPI.

## Pré-requisitos

- Node.js e npm;
- Python 3.10 ou superior e [uv](https://docs.astral.sh/uv/getting-started/installation/) para o backend.

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

Execute a suíte e gere um relatório de cobertura sem limite mínimo:

```bash
uv run --locked python -m pytest
uv run --locked python -m pytest --cov=main --cov-report=term-missing
```
