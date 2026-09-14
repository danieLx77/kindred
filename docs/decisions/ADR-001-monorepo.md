# ADR-001 — Uso de monorepo

## Status

Accepted

## Contexto

O Kindred possui, no MVP, ao menos dois componentes desenvolvidos pela mesma equipe e pertencentes ao mesmo produto: uma aplicação frontend e uma API backend. O projeto também possui documentação de requisitos, arquitetura, testes e decisões técnicas que evoluem em conjunto com o código.

Era necessário decidir se frontend e backend seriam mantidos em repositórios independentes ou em um único repositório.

A equipe é composta inicialmente por dois desenvolvedores, e alterações podem envolver simultaneamente contratos da API, frontend, testes e documentação.

## Decisão

Adotar um **monorepo** para o Kindred.

A estrutura de alto nível será semelhante a:

```text
kindred/
├── frontend/
├── backend/
├── docs/
├── .github/
├── LICENSE
└── README.md
```

Frontend e backend permanecerão módulos independentes dentro do mesmo repositório, com seus próprios processos de build e testes.

## Alternativas consideradas

### Repositórios separados

Manter frontend e backend em repositórios diferentes.

**Vantagens:**
- isolamento completo de pipelines e histórico;
- permissões e ciclos de release podem evoluir independentemente;
- adequado para equipes ou produtos independentes.

**Desvantagens:**
- maior overhead para uma equipe pequena;
- mudanças de contrato podem exigir PRs coordenados em múltiplos repositórios;
- documentação do produto ficaria fragmentada;
- rastreabilidade entre alterações relacionadas seria menos direta.

### Monorepo

Manter frontend, backend e documentação no mesmo repositório.

**Vantagens:**
- visão única do produto;
- alterações frontend/backend podem ser revisadas conjuntamente;
- documentação permanece próxima ao código;
- simplifica onboarding e colaboração;
- facilita rastreabilidade entre requisito, implementação e testes.

**Desvantagens:**
- CI precisa distinguir componentes afetados;
- crescimento futuro pode aumentar o custo dos pipelines;
- exige disciplina para preservar fronteiras entre frontend e backend.

## Consequências

### Positivas

- Um único ponto de entrada para desenvolvimento e documentação.
- Issues e Pull Requests podem representar mudanças completas de produto.
- Facilita colaboração entre os dois desenvolvedores.
- Simplifica versionamento inicial e configuração do GitHub.
- Permite compartilhar configurações de engenharia quando apropriado.

### Negativas

- Pipelines deverão evitar executar tarefas desnecessárias conforme o projeto crescer.
- Frontend e backend não devem se tornar acoplados apenas por estarem no mesmo repositório.
- Caso os componentes adquiram ciclos de vida muito diferentes, a decisão poderá precisar ser revista.

## Notas

Monorepo é uma decisão de organização do código e não implica compartilhar dependências ou misturar responsabilidades entre frontend e backend.
