# ADR-003 — Python e FastAPI no backend

## Status

Accepted

## Contexto

O Kindred necessita de um backend para proteger credenciais da integração externa, fornecer contratos próprios ao frontend, validar entradas, normalizar dados e centralizar tratamento de falhas.

Era necessário escolher uma tecnologia para implementar essa API.

Entre as alternativas consideradas estão Python com FastAPI e Node.js com TypeScript.

## Decisão

Utilizar **Python com FastAPI** para implementar a Kindred API.

O backend será organizado de forma modular, separando responsabilidades de API, aplicação, domínio e integração externa sem aplicar camadas ou abstrações que não tenham utilidade concreta.

## Alternativas consideradas

### Node.js + TypeScript

**Vantagens:**
- mesma linguagem do frontend;
- compartilhamento de conhecimento entre as duas aplicações;
- ecossistema maduro para APIs web.

**Desvantagens:**
- compartilhar a linguagem não elimina a necessidade de contratos entre frontend e backend;
- não apresentou vantagem suficiente, para o escopo atual, para determinar a escolha.

### Python + FastAPI

**Vantagens:**
- adequado para construção de APIs HTTP;
- validação e modelagem de dados integradas ao ecossistema do framework;
- geração de documentação OpenAPI;
- suporte a código assíncrono para integração HTTP;
- boa testabilidade;
- favorece contratos explícitos de entrada e saída.

**Desvantagens:**
- frontend e backend utilizam linguagens diferentes;
- a equipe precisa manter toolchains distintas;
- uso inadequado de recursos assíncronos pode introduzir complexidade.

## Consequências

### Positivas

- A API terá contratos tipados e validáveis.
- Documentação OpenAPI poderá ser gerada a partir da aplicação.
- Integrações HTTP poderão ser encapsuladas de forma testável.
- O backend poderá evoluir independentemente dos detalhes do frontend.

### Negativas

- O repositório possuirá ecossistemas Python e Node.
- CI deverá configurar ambientes distintos.
- Modelos TypeScript e Python não serão compartilhados diretamente.

## Notas

A escolha de FastAPI não implica adoção de uma arquitetura complexa. A estrutura deverá continuar guiada pelos casos de uso e princípios definidos em `architecture.md`.
