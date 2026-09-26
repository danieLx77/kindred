# Kindred

Aplicação web para descoberta de projetos sociais. O repositório contém um frontend React + TypeScript + Vite e uma API inicial em Python + FastAPI.

## Pré-requisitos

- Node.js e npm;
- Python e pip.

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

O lint executa Oxlint seguido de ESLint; o Oxlint cobre rapidamente as regras suportadas e o ESLint complementa a análise com regras e plugins adicionais. O Oxfmt formata os arquivos. São ferramentas recentes, adotadas para manter verificações locais rápidas sem perder cobertura necessária. Usuários do VS Code também recebem recomendações opcionais de extensão em `.vscode/extensions.json`.

## Backend

Prepare o ambiente virtual e instale as dependências:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate // Linux/MacOS
.venv\Scripts\Activate.ps1 // Windows
python -m pip install -r requirements.txt
```

Execute a API localmente:

```bash
python -m uvicorn main:app --reload
```
