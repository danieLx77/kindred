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

A rota de descoberta está implementada na #15. Exemplo de pesquisa:

```text
GET /api/v1/projects?q=education&page_size=10
```

O contrato do Kindred não precisa reproduzir os parâmetros ou formatos internos da GlobalGiving.

### Detalhe de projeto

`GET /api/v1/projects/{project_id}` retorna os campos do card de descoberta
e acrescenta `need`, `activities`, `long_term_impact`, `region` e
`official_url`. O link oficial é um destino externo. Campos opcionais
indisponíveis retornam nulos. O contrato financeiro RF-12/CA-07 segue pendente.

O ID é uma sequência decimal positiva de até 20 dígitos ASCII. Zeros à
esquerda são aceitos, e o ID na resposta usa a representação canônica.
A URL sem o segmento de ID corresponde à descoberta. Um ID inválido
retorna `422 invalid_request` antes de consultar o provedor. Projeto
inexistente retorna `404 project_not_found`. Uma divergência entre os IDs
solicitado e retornado resulta em `502 provider_failure`.
As demais falhas seguem os códigos compartilhados com a descoberta.
Os schemas de ambas as operações estão em `/openapi.json` e `/docs`.

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

A rota `GET /api/v1/projects` lista o catálogo quando `q` está ausente ou em
branco. A busca recebe até 200 caracteres e normaliza espaços. O parâmetro
`page_size` limita o lote a 1–10 itens (padrão 10). A busca depende dos campos
que o provedor indexa. O contrato está disponível em `/openapi.json` e `/docs`.

Uma busca sem resultados retorna HTTP 200:

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "next_cursor": null
  }
}
```

Os cards contêm ID e, quando disponíveis, título, resumo, URL de imagem,
tema, país e referência de organização (ID e nome). Campos ausentes são
nulos.

Para avançar, envie `next_cursor` como `cursor` com o mesmo texto normalizado
e tamanho de lote. O Explore (#17) guarda os cursores públicos usados em cada
posição e reapresenta o anterior para voltar. A primeira página é
representada pela ausência de cursor. Ao mudar texto ou tamanho de lote,
reinicie a navegação. A posição é relativa à sequência percorrida e o
retorno a uma página pode reutilizar o cache do backend. O catálogo pode
mudar entre consultas e diferentes páginas podem ter sido obtidas em
momentos diferentes.

O [contrato de descoberta](project-provider-contract.md) fornece a
continuação interna. A API a encapsula com criptografia autenticada, vinculada
à consulta. Cada ciclo de vida da aplicação gera sua chave de cursor.
Reinícios ou requisições encaminhadas para outro processo exigem reiniciar
a navegação. Para manter a validade dos cursores no MVP, execute uma única
instância com um único worker. O servidor não mantém histórico de navegação.

O valor nulo encerra a navegação. Na pesquisa, um lote com itens pode
ter continuação mesmo quando já contém o último resultado. A próxima
requisição pode retornar um lote vazio, sem nova continuação. O Kindred
não faz chamadas antecipadas nem informa total de itens ou páginas.

Os erros retornam um objeto com o campo `code`:

| HTTP | Código | Motivo |
| --- | --- | --- |
| 400 | `invalid_cursor` | Cursor inválido, de outra consulta ou de um ciclo de vida anterior |
| 422 | `invalid_request` | Parâmetros inválidos |
| 500 | `internal_error` | Falha inesperada na API |
| 502 | `provider_failure` | Falha de transporte, resposta inválida ou operação rejeitada pelo provedor |
| 503 | `provider_unavailable` | Provedor indisponível ou credenciais ausentes ou inválidas |
| 503 | `provider_rate_limited` | Limite de requisições do provedor |
| 504 | `provider_timeout` | Prazo de resposta do provedor excedido |

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

Cada ciclo de vida do FastAPI cria um `GlobalGivingProjectProvider` com um
cliente HTTP e um `DiscoveryCache` próprios. O cache atende apenas à descoberta
pública. A API autentica o cursor público e o adaptador valida a assinatura e
a vinculação da continuação interna antes de acessar o cache. A chave combina a
`DiscoveryQuery` completa (incluindo texto já normalizado pela API e tamanho de
página) com posição, deslocamento e indicação do próximo lote. Cada instância
tem credencial, URL e chaves de assinatura próprias, por isso esses dados não
entram na chave. A API emite um novo cursor público encapsulando a continuação
armazenada, quando houver.

O cache guarda `DiscoveryResult` imutáveis com os projetos em ordem, variantes
de imagem e continuação interna, incluindo respostas vazias válidas. O TTL
padrão é 600 segundos a partir da conclusão, sem renovação por acesso.
Entradas vencidas são removidas quando consultadas ou removidas pela política
de limite. Os limites são 256 entradas por padrão e aproximadamente 16 MiB
de objetos retidos por instância. A política LRU remove primeiro a entrada
usada há mais tempo e resultados individuais acima do orçamento são retornados
sem armazenamento. A estimativa não representa a memória total do processo.
As configurações de TTL e capacidade estão no [README](../../README.md#cache-de-descoberta-no-backend).

Cada chave em falta tem uma operação compartilhada com `asyncio.shield`.
Chaves distintas podem executar em paralelo, com até 256 cargas ativas por
cache. Cancelar o consumidor não cancela a carga. No encerramento, o adaptador
cancela e aguarda as cargas antes de fechar o cliente HTTP. Falhas são
propagadas aos consumidores atuais e a próxima requisição pode tentar de
novo. Falhas na consulta opcional de imagens continuam retornando o card
com a imagem disponível, sem reaproveitar esse resultado em acessos futuros.
Em hits, o backend evita as chamadas de catálogo, busca ou imagens daquela
página. Em misses, continuam valendo a sobreposição de lotes e a recuperação
de timeout da busca.

Os logs em nível DEBUG registram eventos de cache, contadores acumulados de
hits, misses, expirações, remoções e junções, totais de entradas e operações
ativas, bytes estimados e tempos de resolução e de resposta da API.
`provider_operations_avoided` soma hits e junções. Uma operação evitada pode
corresponder a várias chamadas HTTP. O evento `upstream_attempt` registra cada
tentativa HTTP separadamente, inclusive retries. Os eventos omitem chaves do
cache, parâmetros e dados de projetos. O log de acesso do Uvicorn omite a
query string da rota de descoberta.

O cache é por processo e complementa o cache por aba da Explore. Reiniciar o
FastAPI descarta entradas e chaves de cursor. Workers e réplicas independentes
têm caches e chaves próprios. O MVP usa um único worker para manter a
continuidade da navegação. O cache não estabelece um snapshot do catálogo e
páginas podem refletir momentos diferentes dentro do TTL.

O benchmark de descoberta roda com o FastAPI em processo e transporte HTTPX
simulado. Execute `uv run --locked python discovery_cache_benchmark.py` na
pasta `backend/`. Para repetir a linha de base, copie o script para fora do
repositório e execute `PYTHONPATH=. uv run --locked python /caminho/do/script.py
--baseline` a partir de `backend/` de um checkout anterior ao cache.

### Primeira página antecipada da Explore

| Estratégia | Primeiro acesso | Após reinício | Atualização | Complexidade e operação | Consumo externo | Falhas | Consistência e paginação |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Aquecimento no startup | Aguarda se o usuário chegar antes do aquecimento | Repete a consulta de origem | Uma vez por partida | Um trabalho no lifespan | Uma carga por reinício | Fluxo dinâmico se a carga falhar | Cursores emitidos pelo processo atual |
| Aquecimento periódico em memória | Rápido depois da primeira carga | Depende de uma nova carga | Intervalo controlado | Uma tarefa por processo | Uma carga por intervalo e processo | Dados disponíveis até o limite em memória | Cursores emitidos pelo processo atual |
| Snapshot persistente com atualização periódica | Imediato quando há snapshot válido | Reaproveita o arquivo do volume | Intervalo controlado e limite de idade | Arquivo pequeno e volume gravável | Uma carga por intervalo. Reiniciar com snapshot novo adia a carga | Preserva a última versão válida até expirar | Assinatura local e confirmação de ordem na passagem para a segunda página |

O MVP usa um snapshot opcional do backend. O repositório define CI e um
Dockerfile de desenvolvimento. A hospedagem de produção, o volume de produção
e o agendamento externo ainda não estão definidos. Um volume Docker nomeado
ou um diretório persistente permite reutilizar os dados entre contêineres ou
processos. O Vite constrói o frontend sem credenciais da GlobalGiving e a CI
usa transportes simulados. Cada instância habilitada tem uma tarefa de
atualização no lifespan. Use um worker e um escritor por volume.

O arquivo JSON tem esquema versionado, provedor, timestamp, cards públicos e
um indicador de continuação e, quando disponível, uma pista numérica para o
lote seguinte. Arquivos anteriores sem a pista continuam legíveis. A validação
rejeita campos desconhecidos, registros duplicados, páginas incompletas com
continuação e arquivos acima de 128 KiB. Na geração, URLs de imagem
inválidas, com credenciais, parâmetros ou fragmentos são omitidas do card
sem remover os demais dados. Na leitura, o schema continua rejeitando
arquivos que contenham uma URL inadequada. O adaptador mapeia a resposta
pelas mesmas rotinas de descoberta da Fase 1. A geração escreve em um arquivo
temporário no mesmo diretório e publica com substituição atômica. O arquivo
guarda os dados públicos dos cards e a pista opcional. Chaves, URLs
autenticadas e cursores ficam fora do arquivo.

A rota pública autentica a continuação vinda do cliente. Para o catálogo
inicial de nove itens, um snapshot válido prevalece sobre o cache dinâmico.
No processo atual, o adaptador assina uma continuação que vincula o
deslocamento ao resumo criptográfico dos IDs ordenados apresentados. Ao
avançar, a primeira carga do segundo lote confere esses IDs no catálogo,
consome a sobra do lote atual e segue usando o `nextProjectId` observado na
mesma leitura. A pista pode antecipar a segunda consulta em paralelo, mas o
resultado só é aceito se a ordem e a posição forem confirmadas pelo primeiro
lote. Se apenas a posição divergir, o adaptador descarta a consulta
especulativa e usa a posição atual. Se os primeiros IDs mudaram, a API
retorna `400 invalid_cursor`, o backend descarta o snapshot correspondente e a
Explore permite voltar à primeira página. O descarte avança a geração do
snapshot, bloqueando publicações iniciadas na geração anterior. A geração
também faz parte da chave single-flight da primeira página, portanto a
recuperação pode usar uma carga atual mesmo com uma atualização antiga
pendente. O `DiscoveryCache` pode reutilizar uma segunda página já
validada dentro do TTL.
Depois de um reinício, abrir novamente a primeira página emite um novo
cursor. A GlobalGiving pode mudar o catálogo entre chamadas e a navegação
continua sujeita a essas mudanças.

Após ler o arquivo, o FastAPI agenda a primeira atualização para quando o
snapshot completar o intervalo de atualização, ou imediatamente se faltar
um arquivo utilizável. Usuários com um snapshot válido recebem os cards
durante a atualização. Uma carga em andamento e visitantes sem snapshot
compartilham a mesma operação de descoberta no `DiscoveryCache`. Se a
atualização falhar, os cards anteriores ficam disponíveis até 1800 segundos
de idade. Após esse limite, vale o fluxo dinâmico e seus códigos de erro.
Uma nova tentativa periódica ocorre somente após o intervalo configurado.
O lifespan cancela e drena a atualização e a carga compartilhada antes de
fechar o cliente HTTP. O cache de navegação da Explore ainda pode servir uma
página dentro dos seus 60 segundos próprios.

A GlobalGiving orienta a minimizar chamadas e atualizar dados em cache por
expiração ou ausência. O intervalo padrão acompanha a duração de 600
segundos da Fase 1. A janela de 30 minutos é uma decisão do projeto para
tolerar falhas transitórias. [Código de conduta da API](https://www.globalgiving.org/api/legal/code-of-conduct/)
e [termos de uso](https://www.globalgiving.org/api/legal/terms-of-service/).

O benchmark usa `uv run --locked python explore_snapshot_benchmark.py` em
`backend/`. Para medir a base, copie o script para fora do repositório e
execute `PYTHONPATH=. uv run --locked python /caminho/do/script.py --before`
em `backend/` do checkout da Fase 1. Para comparar duas revisões da Fase 2,
execute a mesma cópia externa em cada checkout, sem `--before`. Os cenários
incluem avanço para a segunda e a terceira página, catálogo alterado e
recuperação após invalidação. O transporte de teste simula latências
e indisponibilidade. Os eventos `explore_snapshot` permitem conferir idade,
duração de atualização e falhas sem emitir dados de projeto.

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
- cache compartilhado de descoberta por processo.

Essas escolhas não devem ser realizadas apenas por popularidade; devem considerar requisitos, complexidade e trade-offs.

## 24. Histórico

| Versão | Status | Descrição |
|---|---|---|
| 0.1 | Draft | Arquitetura inicial do MVP |
