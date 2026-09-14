# Kindred — Arquitetura de Software

**Versão:** 0.1  
**Status:** Draft  
**Escopo:** MVP  
**Documento relacionado:** `docs/requirements/software-requirements.md`

---

## 1. Objetivo

Este documento descreve a arquitetura de software proposta para o MVP do **Kindred**, incluindo seus componentes principais, responsabilidades, fronteiras, integrações, fluxos, princípios e decisões que deverão ser detalhadas em Architecture Decision Records (ADRs).

O objetivo arquitetural é atender aos requisitos do MVP mantendo simplicidade, segurança, testabilidade, manutenibilidade e capacidade de evolução.

## 2. Princípios arquiteturais

**PA-01 — Simplicidade.** Utilizar a solução menos complexa que satisfaça os requisitos atuais.

**PA-02 — Separação de responsabilidades.** Apresentação, aplicação, domínio e integração externa devem possuir responsabilidades distintas.

**PA-03 — Inversão de dependência.** As regras da aplicação não devem depender diretamente dos detalhes de implementação da GlobalGiving.

**PA-04 — Security by Design.** Credenciais e informações sensíveis devem ser protegidas desde o desenho da solução.

**PA-05 — Testabilidade.** Componentes devem permitir substituição de dependências externas por doubles de teste.

**PA-06 — Observabilidade.** Falhas relevantes devem ser diagnosticáveis sem exposição de informações sensíveis.

**PA-07 — Accessibility by Design.** Acessibilidade deve ser considerada durante a implementação, e não apenas ao final.

**PA-08 — Arquitetura evolutiva.** Banco de dados, cache distribuído, filas e outros componentes só deverão ser adicionados quando houver necessidade concreta e documentada.

## 3. Visão geral

A arquitetura do MVP será composta por três elementos principais:

1. **Frontend Kindred** — aplicação web responsável pela experiência do usuário.
2. **Kindred API** — backend intermediário responsável pelas regras de aplicação e integração externa.
3. **GlobalGiving API** — fonte externa principal dos dados de projetos e organizações.

```text
Usuário
   |
 HTTPS
   v
Frontend Kindred
   |
 REST / JSON
   v
Kindred API
   |
 HTTPS
   v
GlobalGiving API
```

O frontend não deverá consumir a GlobalGiving diretamente.

## 4. C4 — Nível 1: Contexto do sistema

### Pessoas

**Visitante**  
Pessoa que utiliza o Kindred para pesquisar, filtrar e conhecer projetos e organizações sociais.

### Sistemas

**Kindred**  
Sistema de descoberta de projetos sociais.

**GlobalGiving**  
Sistema externo que fornece os dados utilizados pelo Kindred.

```text
+-----------+       utiliza       +-------------+
| Visitante | ------------------> |   Kindred   |
+-----------+                      +------+------+
                                          |
                                          | consulta dados
                                          v
                                  +---------------+
                                  | GlobalGiving  |
                                  +---------------+
```

## 5. C4 — Nível 2: Containers

```text
+-----------+
| Visitante |
+-----+-----+
      |
      | HTTPS
      v
+----------------------------+
| Frontend                   |
| React + TypeScript         |
|                            |
| UI, routing, i18n, estado, |
| acessibilidade e API client|
+-------------+--------------+
              |
              | REST / JSON
              v
+----------------------------+
| Kindred API                |
| Python + FastAPI           |
|                            |
| Aplicação, domínio,        |
| validação e integrações    |
+-------------+--------------+
              |
              | HTTPS
              v
+----------------------------+
| GlobalGiving API           |
| Sistema externo            |
+----------------------------+
```

### 5.1 Frontend

Responsabilidades:
- renderização da interface;
- navegação;
- busca, filtros e paginação;
- internacionalização PT-BR/EN;
- responsividade;
- acessibilidade;
- feedback de loading, erro e ausência de resultados;
- comunicação exclusivamente com a Kindred API.

Stack inicialmente proposta:
- React;
- TypeScript;
- Vite;
- React Router;
- biblioteca de gerenciamento de server state a ser definida;
- biblioteca de i18n a ser definida.

### 5.2 Kindred API

Responsabilidades:
- expor a API interna do produto;
- validar entradas;
- executar casos de uso;
- proteger credenciais externas;
- consumir a GlobalGiving;
- normalizar dados externos;
- mapear erros externos para erros do domínio/API;
- fornecer contratos estáveis ao frontend;
- produzir informações de observabilidade.

Stack inicialmente proposta:
- Python;
- FastAPI;
- cliente HTTP compatível com execução assíncrona;
- validação baseada nos modelos da aplicação.

### 5.3 GlobalGiving

Responsabilidades externas:
- fornecer projetos;
- fornecer organizações;
- fornecer temas, países/regiões e demais metadados disponíveis;
- fornecer imagens, informações financeiras e links quando presentes.

A GlobalGiving é uma dependência externa e não pertence ao domínio do Kindred.

## 6. C4 — Nível 3: Componentes do backend

```text
HTTP
 |
 v
+-------------+
| API Routes  |
+------+------+
       |
       v
+----------------------+
| Application Services |
| / Use Cases          |
+----------+-----------+
           |
           v
+----------------------+
| Port / Interface     |
| External Provider    |
+----------+-----------+
           ^
           |
+----------+-----------+
| GlobalGiving Adapter |
| Client + Mapper      |
+----------+-----------+
           |
           v
     GlobalGiving
```

### API

Responsável pelo protocolo HTTP:
- rotas;
- parâmetros;
- status codes;
- serialização;
- dependências HTTP.

### Application

Responsável pela orquestração dos casos de uso:
- pesquisar projetos;
- obter projeto;
- obter organização;
- listar projetos da organização;
- consultar catálogos.

### Domain

Representa conceitos próprios do Kindred, como:
- Project;
- Organization;
- Theme;
- Location;
- FinancialProgress;
- paginação.

O domínio não deve conhecer schemas específicos da GlobalGiving.

### Integrations

Contém detalhes da integração externa:
- autenticação;
- requisições HTTP;
- schemas externos;
- conversão;
- tratamento de erros da GlobalGiving.

## 7. Estrutura lógica proposta

```text
kindred/
├── frontend/
│   ├── src/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── integrations/
│   │   │   └── globalgiving/
│   │   ├── core/
│   │   └── main.py
│   └── tests/
├── docs/
│   ├── requirements/
│   ├── architecture/
│   ├── decisions/
│   ├── testing/
│   └── contributing/
├── .github/
│   └── workflows/
└── README.md
```

A estrutura final poderá ser refinada durante a implementação. O objetivo é preservar as fronteiras, não impor uma hierarquia artificial de diretórios.

## 8. API interna

Contrato conceitual inicial:

```text
GET /api/v1/projects
GET /api/v1/projects/{project_id}

GET /api/v1/organizations/{organization_id}
GET /api/v1/organizations/{organization_id}/projects

GET /api/v1/themes
GET /api/v1/countries
GET /api/v1/regions

GET /api/v1/health
```

Exemplo de pesquisa:

```text
GET /api/v1/projects?q=education&theme=edu&country=BR&page=2
```

O contrato do Kindred não precisa reproduzir os parâmetros ou formatos internos da GlobalGiving.

## 9. Anti-Corruption Layer

A integração com GlobalGiving deverá funcionar como uma camada de proteção entre os modelos externos e o domínio.

```text
GlobalGiving Response
        |
        v
External Schema
        |
        v
Mapper
        |
        v
Kindred Domain Model
        |
        v
API Response
```

Benefícios:
- desacoplamento;
- testabilidade;
- estabilidade dos contratos internos;
- possibilidade de substituir/adicionar fontes no futuro;
- tratamento centralizado de campos ausentes;
- redução do impacto de mudanças externas.

## 10. Fluxo de busca

```text
Visitante
   |
   v
Frontend
   |
   | GET /api/v1/projects?... 
   v
API Route
   |
   v
Search Projects Use Case
   |
   v
External Provider Port
   |
   v
GlobalGiving Adapter
   |
   v
GlobalGiving API
   |
   v
External Schema -> Mapper -> Domain
   |
   v
Response DTO
   |
   v
Frontend
```

## 11. Paginação

A paginação exposta pelo Kindred deverá utilizar uma abstração amigável ao frontend.

Exemplo:

```json
{
  "items": [],
  "pagination": {
    "page": 2,
    "pageSize": 10,
    "hasNext": true
  }
}
```

O adapter será responsável por converter esse modelo para o mecanismo utilizado pelo provedor externo.

## 12. Internacionalização

### Interface

O MVP suportará:
- `pt-BR`;
- `en`.

Textos da interface deverão utilizar recursos de internacionalização e não ficar espalhados como strings hardcoded.

### Conteúdo externo

Conteúdo proveniente da GlobalGiving será apresentado no idioma disponibilizado pela fonte.

Tradução automática do conteúdo externo não faz parte do MVP.

## 13. Segurança

### Credenciais

Credenciais da GlobalGiving deverão existir apenas no ambiente do backend.

É proibido:
- incluir segredos no bundle frontend;
- versionar `.env` contendo segredos;
- registrar segredos em logs;
- enviar credenciais ao navegador.

### Comunicação

Em produção:
- frontend e backend deverão utilizar HTTPS;
- backend e GlobalGiving deverão comunicar-se por HTTPS.

### Entrada

Entradas externas deverão ser validadas antes de atingir os casos de uso.

### Erros

Respostas públicas não devem expor:
- stack traces;
- tokens;
- chaves;
- detalhes internos desnecessários.

## 14. Persistência

O MVP não utilizará banco de dados próprio.

Justificativa:
- projetos são fornecidos pela GlobalGiving;
- organizações são fornecidas pela GlobalGiving;
- não há contas;
- não há favoritos persistentes;
- não há histórico ou conteúdo próprio.

A introdução de persistência exigirá revisão arquitetural e ADR.

## 15. Cache

Não haverá cache distribuído inicialmente.

A necessidade deverá ser avaliada com base em:
- latência;
- limites do provedor;
- volume;
- disponibilidade;
- custo operacional.

Caso necessário, poderão ser avaliados cache em memória e posteriormente soluções distribuídas.

## 16. Tratamento de falhas

A Kindred API deverá distinguir, quando aplicável:
- entrada inválida;
- recurso inexistente;
- falha do provedor externo;
- timeout;
- erro interno.

O frontend deverá converter essas situações em estados compreensíveis.

A indisponibilidade da GlobalGiving não deve causar falha não controlada da interface.

## 17. Observabilidade

O MVP deverá possuir logs adequados para diagnóstico.

Campos úteis incluem:
- request ID;
- método;
- rota;
- status;
- duração;
- categoria do erro.

Segredos e dados sensíveis não deverão ser registrados.

Ferramentas externas de tracing/error tracking poderão ser avaliadas posteriormente.

## 18. Testabilidade

A aplicação deverá permitir substituição do provider real por doubles.

```text
Production:
Application -> GlobalGivingAdapter -> GlobalGiving

Tests:
Application -> FakeExternalProvider
```

Chamadas HTTP ao provedor não devem estar espalhadas pelas regras de aplicação.

Testes de integração específicos validarão o adapter.

## 19. Deployment

Modelo conceitual:

```text
Internet
   |
   v
Frontend / CDN
   |
   | HTTPS
   v
Backend API
   |
   | HTTPS
   v
GlobalGiving
```

O provedor de hospedagem será decidido posteriormente.

## 20. Containerização

Docker será utilizado para tornar o ambiente do backend reproduzível e facilitar:
- desenvolvimento;
- onboarding;
- CI;
- deploy.

Containerização não implica adoção de orquestração complexa.

## 21. CI/CD

O pipeline deverá possuir quality gates independentes para frontend e backend.

```text
Pull Request
     |
 +---+---+
 |       |
 v       v
Frontend Backend
 |       |
lint    lint
type    type
test    test
build   test/build
 |       |
 +---+---+
     |
     v
Merge elegível
```

O detalhamento será definido em `test-strategy.md` e `contributing/workflow.md`.

## 22. Decisões arquiteturais a registrar

ADRs inicialmente previstos:

- ADR-001 — Uso de monorepo;
- ADR-002 — React + TypeScript no frontend;
- ADR-003 — Python + FastAPI no backend;
- ADR-004 — Backend intermediário entre frontend e GlobalGiving;
- ADR-005 — Ausência de banco de dados no MVP;
- ADR-006 — GlobalGiving como fonte externa principal;
- ADR-007 — Modelo de domínio próprio e Anti-Corruption Layer;
- ADR-008 — REST/JSON entre frontend e backend;
- ADR-009 — Estratégia de internacionalização;
- ADR-010 — C4 Model para documentação arquitetural.

## 23. Decisões ainda abertas

Ainda deverão ser avaliados:
- biblioteca de server state;
- biblioteca de i18n;
- cliente HTTP do backend;
- ferramenta de testes E2E;
- hospedagem frontend/backend;
- estratégia de error tracking;
- metas quantitativas de performance;
- eventual cache.

Essas escolhas não devem ser realizadas apenas por popularidade; devem considerar requisitos, complexidade e trade-offs.

## 24. Histórico

| Versão | Status | Descrição |
|---|---|---|
| 0.1 | Draft | Arquitetura inicial do MVP |
