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

### Explore com o backend local

Inicie a API em um terminal. Configure `GLOBALGIVING_API_KEY` conforme
[a configuração local do backend](#configuração-local):

```bash
cd backend
uv sync --locked
uv run --locked uvicorn main:app --host 127.0.0.1 --port 8000
```

Em outro terminal, inicie o frontend:

```bash
cd frontend
npm ci
npm run dev
```

Abra `/explore` na URL do Vite. O proxy de desenvolvimento encaminha
`/api` para `http://127.0.0.1:8000`. Para mudar o destino local,
defina `KINDRED_API_TARGET` ao iniciar o Vite. O cliente usa caminhos
relativos no frontend e a chave do provedor permanece no backend.

A busca usa `q` na URL. Ao avançar, o Explore guarda o cursor anterior
no histórico do navegador. Um link intermediário aberto em outro
histórico permite voltar à primeira página. Reinícios da API podem
invalidar cursores, e a interface oferece retorno à primeira página
preservando a busca.

A Explore mantém até 12 páginas visitadas em memória por aba, por 60 segundos
a partir da resposta. A chave inclui a consulta, o tamanho da página e o
cursor. Voltar a uma página em cache reutiliza seus resultados, inclusive
ao retornar de um detalhe. Uma resposta de cursor inválido limpa o cache
para que o retorno à primeira página solicite uma continuação nova.

### Jornada de descoberta e detalhes

Na Home, envie uma busca. Na Explore, abra um card para consultar
`/projects/:id`. A página de detalhes preserva a busca e a posição ao voltar
para Explore quando a visita começou em um card. Acessos diretos retornam
ao catálogo. O link oficial, identificado como externo, aparece quando
fornecido pela API e válido.

### Bandeiras do seletor de idioma

Os arquivos `br.svg` e `us.svg` em `frontend/src/assets/flags/` são cópias da
[variante retangular do flag-icons v7.3.2](https://github.com/lipis/flag-icons/tree/v7.3.2/flags/4x3).
O [aviso MIT original](frontend/public/licenses/flag-icons.txt) acompanha os assets
na distribuição do frontend.

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

### Configuração local

Em um checkout de desenvolvimento, copie `.env.example` para `.env` na
**raiz do repositório** e preencha `GLOBALGIVING_API_KEY` no arquivo. Essa
é a variável necessária para listar, pesquisar e consultar detalhes de projetos.
O arquivo `.env` é ignorado pelo Git.

Inicie a API em `backend/` com `uv run --locked uvicorn main:app --reload`.
Durante a inicialização, a aplicação localiza o arquivo a partir de
`backend/main.py`. Uma variável exportada tem prioridade, inclusive se
estiver vazia. Depois de alterar a configuração, reinicie o backend.

Em CI e em implantações sem checkout Git, forneça a chave pelo ambiente
de execução. Se a produção usar um checkout Git, defina
`KINDRED_LOAD_LOCAL_ENV=0` para desativar a leitura local. No Docker,
forneça a chave ao contêiner pelo ambiente de execução.

Sem chave, a rota raiz continua disponível e os endpoints de projetos retornam
`503` com o código `provider_unavailable`. Esse código também pode indicar
falha de autenticação ou indisponibilidade do provedor. Para diagnosticar,
confirme a presença da variável no ambiente ou no arquivo da raiz e consulte
`http://127.0.0.1:8000/api/v1/projects`. Compartilhe somente o status HTTP e
o código de erro retornado pelo Kindred.

### Descoberta GlobalGiving (issue #12)

`integrations.globalgiving.GlobalGivingDiscoveryAdapter` implementa a operação
`discover` do contrato de projetos da #10. O provider completo é
`integrations.globalgiving.GlobalGivingProjectProvider`, que também implementa
a consulta detalhada da #13 com o mesmo cliente HTTP.
A API da #15 reutiliza uma instância por ciclo de vida da aplicação e
fecha o cliente ao encerrar o FastAPI.

O startup do backend resolve `GLOBALGIVING_API_KEY` e passa a chave ao
provider. A URL base padrão é HTTPS, o timeout
total e por fase é 10 segundos, a resposta é limitada a 2 MiB e não há retries
nem redirecionamentos automáticos. HTTPX agora é dependência de execução.
Logs HTTPX/HTTPcore são suprimidos apenas no contexto dessas chamadas, inclusive
leitura e fechamento, para não registrar a chave exigida na query string. O
cliente próprio não instala hooks de tracing nem usa proxies do ambiente.

A API de descoberta aceita `page_size` de 1 a 10, com padrão 10. A Explore solicita
9 projetos por página. Na listagem, os lotes externos de até 10 projetos são retomados
com a mesma posição externa e um deslocamento interno. Quando a sobra de um lote não
preenche a página e há continuação, o adapter busca o próximo lote para completá-la.
Uma resposta do provedor com menos itens ainda pode produzir uma página parcial.
Na busca, qualquer lote não vazio permite tentar a próxima posição; apenas uma
resposta vazia confirma o fim, independentemente de `numberFound`. Isso pode
exigir uma chamada adicional no final. Não há garantia de snapshot estável.

Os cards preferem a variante `large` da GlobalGiving quando disponível.
Quando a resposta entrega apenas a miniatura padrão, o adapter pode buscar
variantes em uma única consulta adicional para os projetos da página exibida.
Essa consulta tem limite de 2 segundos e preserva as miniaturas se falhar.

Quando uma página precisa usar dois lotes do catálogo e a continuação anterior
já informou o segundo lote, as duas consultas são iniciadas em paralelo. O
adapter confirma a posição com a resposta atual antes de usar o segundo lote.
Na busca textual, um timeout permite uma única nova tentativa no tempo restante
do orçamento original de 10 segundos. O adapter reserva 20% desse orçamento
para a nova tentativa e respeita respostas de limite de taxa sem repeti-las.

As continuações são estado interno assinado, vinculado à consulta e à instância,
sem armazenamento de páginas. Permitem replay enquanto a instância existir;
reinício ou outra instância invalida o handle. A assinatura impede adulteração,
mas não é criptografia: esses tokens internos não devem ser publicados diretamente
pela API pública. Filtros de tema/país ainda são rejeitados explicitamente.

A #10 deixou categorias de falhas para a integração. A decisão nesta entrega é
usar `projects.errors.ProviderError` com `ProviderFailure`: entrada inválida,
autenticação, recurso ausente, indisponibilidade, limite de taxa, timeout, rede
ou resposta inválida. Não carrega URL, corpo ou exceção bruta. Um 404 de descoberta
é falha da operação, não uma lista vazia. A rota pública da #15 traduz essas
categorias em códigos HTTP.
Campos opcionais inválidos são omitidos; ID de projeto inválido rejeita o lote.
Organização sem ID utilizável não gera referência fictícia.

### Detalhe GlobalGiving (issue #13)

`get_project(id)` recebe um ID textual numérico positivo, consulta diretamente
o projeto e retorna `ProjectDetail`. Um 404 retorna `None`; 410, timeout e outras
falhas externas mantêm as categorias de erro da integração. Campos opcionais
sem dados utilizáveis são omitidos. O link oficial vem de `projectLink`, e a
imagem prioriza a variante `extraLarge`, com fallback para outras imagens
fornecidas pelo provedor. O
adapter não consulta a galeria nem interpreta os valores financeiros do provedor.

A API da #16 expõe `GET /api/v1/projects/{project_id}`. O detalhe usa o
mesmo cliente da descoberta e retorna 404 para projeto inexistente.
Consulte `/docs` e o
[contrato de detalhe](docs/architecture/architecture.md#detalhe-de-projeto).

### API de descoberta (issue #15)

`GET /api/v1/projects` lista projetos e `GET /api/v1/projects?q=education`
faz pesquisa textual. Consulte `/docs` e o
[contrato de paginação e erros](docs/architecture/architecture.md#11-paginação).
Configure `GLOBALGIVING_API_KEY` conforme a [configuração local](#configuração-local).

Os testes de integração usam RESPX com requisições não previstas bloqueadas,
transportes locais e uma chave fictícia. Não exigem acesso real à GlobalGiving.

Execute a suíte e gere um relatório de cobertura sem limite mínimo:

```bash
uv run --locked python -m pytest
uv run --locked python -m pytest --cov=main --cov-report=term-missing
```

Para desenvolver o backend sem instalar Python e uv no host, use o ambiente Docker descrito no [workflow de contribuição](docs/contributing/workflow.md#backend-com-docker).
