# Kindred — Estratégia de Testes

**Versão:** 0.1  
**Status:** Draft  
**Escopo:** MVP  
**Documentos relacionados:** `software-requirements.md`, `architecture.md`

---

## 1. Objetivo

Este documento define a estratégia de qualidade e testes do MVP do **Kindred**.

A estratégia busca:
- reduzir risco de regressões;
- validar requisitos e critérios de aceitação;
- fornecer feedback rápido durante desenvolvimento;
- proteger a branch principal;
- validar a integração com a GlobalGiving sem tornar a suíte dependente do serviço externo;
- apoiar requisitos de acessibilidade, responsividade, segurança e performance.

O objetivo não é maximizar quantidade de testes ou percentual de cobertura, mas obter confiança proporcional ao risco.

## 2. Princípios

**PT-01 — Testar comportamento, não implementação.**  
Testes devem preferir contratos e comportamentos observáveis a detalhes internos.

**PT-02 — Feedback rápido.**  
Testes baratos e rápidos devem executar com maior frequência.

**PT-03 — Isolamento de terceiros.**  
A maior parte da suíte não deve depender da disponibilidade da GlobalGiving.

**PT-04 — Pirâmide pragmática.**  
A suíte deverá possuir muitos testes unitários/de componente, quantidade moderada de integração e poucos E2E de alto valor.

**PT-05 — Rastreabilidade.**  
Critérios de aceitação relevantes devem possuir forma explícita de validação.

**PT-06 — Qualidade além de testes funcionais.**  
Acessibilidade, performance, segurança, análise estática e build fazem parte da qualidade.

**PT-07 — Sem meta de cobertura vazia.**  
Cobertura será utilizada como indicador e detector de áreas não exercitadas, não como objetivo isolado.

## 3. Pirâmide de testes

```text
                 /\
                /  \
               / E2E\
              /------\
             /Integração\
            /------------\
           / Unidade / UI \
          /________________\
```

### Unidade / componente

Maior volume.

Objetivos:
- regras;
- mappers;
- cálculos;
- validações;
- componentes;
- estados da interface.

### Integração

Objetivos:
- rotas + aplicação;
- contratos;
- adapter GlobalGiving;
- serialização;
- interação entre componentes relevantes.

### E2E

Poucos fluxos críticos completos, executados como um usuário real.

## 4. Escopo

Serão contemplados:
- backend;
- frontend;
- contratos internos;
- integração externa;
- fluxos E2E;
- acessibilidade;
- responsividade;
- performance;
- segurança automatizável;
- internacionalização;
- análise estática;
- build.

Não faz parte desta estratégia testar internamente a implementação da GlobalGiving.

## 5. Estratégia do backend

### 5.1 Testes unitários

Devem validar principalmente:
- casos de uso;
- mapeamento GlobalGiving -> domínio;
- paginação;
- cálculo de progresso financeiro;
- tratamento de campos opcionais;
- validações;
- mapeamento de exceções.

Exemplo conceitual:

```text
Given:
funding = 250
goal = 1000

When:
progresso é calculado

Then:
progress = 25%
```

### 5.2 Test doubles

Casos de uso deverão poder utilizar um provider falso:

```text
Application Service
       |
       +---- production -> GlobalGivingAdapter
       |
       +---- tests ------> FakeExternalProvider
```

Isso permite testar:
- sucesso;
- nenhum resultado;
- timeout;
- erro externo;
- dados incompletos;
- paginação;

sem acesso à internet.

### 5.3 Testes de API

Devem validar:
- status HTTP;
- query/path parameters;
- validação;
- formato das respostas;
- tratamento de erro;
- paginação.

Exemplos:
- `GET /projects` -> 200;
- projeto inexistente -> 404;
- parâmetro inválido -> 4xx apropriado;
- provedor indisponível -> resposta controlada.

### 5.4 Integração GlobalGiving

O adapter deverá possuir testes específicos.

A suíte principal deverá utilizar respostas controladas/fixtures.

Devem existir casos representativos de:
- resposta válida;
- lista vazia;
- campos opcionais ausentes;
- erro de autenticação;
- rate limit, se aplicável;
- timeout;
- erro 5xx;
- payload inesperado.

Chamadas reais ao ambiente externo não devem ser requisito para cada PR.

Um smoke/contract test externo poderá ser executado separadamente se for tecnicamente e operacionalmente adequado.

## 6. Estratégia do frontend

### 6.1 Testes unitários

Adequados para:
- funções utilitárias;
- formatação;
- paginação;
- transformação de parâmetros;
- regras simples de apresentação.

### 6.2 Testes de componentes

Devem testar componentes pelo ponto de vista do usuário.

Exemplos:
- SearchBar permite digitação e submissão;
- filtros refletem seleção;
- ProjectCard apresenta dados relevantes;
- paginação possui estado atual;
- ErrorState oferece retry;
- LanguageSwitcher altera idioma.

Preferir seletores acessíveis, como role, label e texto, evitando dependência de classes CSS.

### 6.3 Mock de rede

Testes do frontend devem simular a Kindred API na camada de rede sempre que possível, em vez de mockar detalhes internos de hooks.

Cenários:
- sucesso;
- loading;
- empty;
- erro;
- resposta parcial.

## 7. Testes E2E

Os testes E2E deverão cobrir somente jornadas críticas.

### E2E-01 — Busca

1. abrir Home;
2. pesquisar uma causa;
3. visualizar resultados;
4. abrir um projeto;
5. visualizar detalhes.

### E2E-02 — Filtros e paginação

1. abrir Explorar;
2. aplicar tema;
3. aplicar localização;
4. validar resultados;
5. mudar página;
6. confirmar preservação dos filtros.

### E2E-03 — Projeto e organização

1. abrir projeto;
2. acessar organização;
3. visualizar informações;
4. abrir projeto associado.

### E2E-04 — Internacionalização

1. abrir aplicação;
2. alternar idioma;
3. navegar;
4. confirmar persistência da preferência.

### E2E-05 — Falha controlada

1. simular indisponibilidade do backend/provedor;
2. validar mensagem;
3. executar retry;
4. validar recuperação.

Os testes E2E devem preferencialmente controlar respostas externas para evitar flakiness.

## 8. Acessibilidade

A conformidade alvo é WCAG 2.2 AA.

### Automatizado

A suíte deverá verificar, quando suportado:
- violações detectáveis automaticamente;
- nomes acessíveis;
- labels;
- roles;
- estrutura básica;
- atributos necessários.

### Manual

Automação não é suficiente.

Antes do release deverão ser validados manualmente:
- navegação apenas por teclado;
- ordem de foco;
- foco visível;
- comportamento de modais/drawers;
- zoom;
- conteúdo em diferentes viewport sizes;
- uso básico com leitor de tela;
- contraste quando não coberto adequadamente por automação.

A validação manual deverá possuir checklist versionado.

## 9. Responsividade e compatibilidade

### Viewports

Os testes deverão contemplar pelo menos categorias representativas de:
- mobile;
- tablet;
- desktop.

Não é necessário testar todos os dispositivos existentes.

### Browsers

Antes do release deverão ser validados navegadores modernos definidos nos requisitos:
- Chrome;
- Firefox;
- Edge;
- Safari.

A matriz exata poderá diferenciar CI automatizado de validação manual conforme custo e infraestrutura.

## 10. Internacionalização

Devem existir testes para:
- PT-BR;
- inglês;
- alternância;
- persistência durante navegação;
- ausência de chaves de tradução visíveis;
- layout com textos de comprimentos diferentes.

Conteúdo externo não deverá ser considerado traduzido pelo Kindred no MVP.

## 11. Performance

### Métricas

O MVP acompanhará:
- LCP;
- INP;
- CLS.

Metas iniciais de referência para experiência considerada boa:
- **LCP <= 2,5 s**;
- **INP <= 200 ms**;
- **CLS <= 0,1**.

Essas metas devem ser interpretadas no contexto de medição apropriado e poderão ser refinadas antes do release.

### Lighthouse

Lighthouse será utilizado como ferramenta de diagnóstico e quality gate complementar.

Proposta inicial para páginas críticas em ambiente controlado:
- Performance >= 90;
- Accessibility >= 90;
- Best Practices >= 90;
- SEO >= 90.

Os scores não substituem métricas reais nem testes manuais.

A equipe deverá revisar estas metas após possuir uma primeira versão funcional, evitando otimizações prematuras.

## 12. Segurança

Verificações deverão incluir:
- nenhum segredo versionado;
- nenhuma credencial exposta ao frontend;
- validação de entrada;
- dependências conhecidamente vulneráveis;
- respostas sem stack trace em produção;
- logs sem segredos.

Ferramentas de dependency scanning poderão integrar o CI.

Testes de segurança aprofundados não fazem parte do MVP, mas vulnerabilidades críticas conhecidas bloqueiam release.

## 13. Análise estática e formatação

### Frontend

O CI deverá executar:
- lint;
- verificação de tipos;
- testes;
- build;
- formatação/check, conforme configuração adotada.

### Backend

O CI deverá executar:
- lint;
- verificação de tipos, se adotada;
- testes;
- análise/formatação definida pela equipe.

As ferramentas concretas serão escolhidas durante bootstrap e registradas quando arquiteturalmente relevantes.

## 14. Cobertura

Não será adotado inicialmente um percentual global arbitrário como sinônimo de qualidade.

A equipe deverá:
- gerar relatório de cobertura;
- acompanhar arquivos críticos não exercitados;
- exigir testes para regras e regressões relevantes;
- evitar testes artificiais criados apenas para elevar percentual.

Após estabilização do MVP, poderá ser definido um threshold mínimo com base na cobertura real e no perfil de risco.

## 15. Testes de regressão

Toda correção de bug relevante deverá, quando tecnicamente viável, incluir um teste que:
1. falharia antes da correção;
2. passe após a correção;
3. permaneça na suíte para evitar regressão.

## 16. Fixtures e dados de teste

Fixtures externas deverão:
- ser pequenas;
- representar cenários reais;
- remover dados desnecessários;
- possuir finalidade clara;
- não conter segredos.

Devem existir fixtures para:
- projeto completo;
- projeto com campos ausentes;
- organização completa;
- organização parcial;
- busca vazia;
- paginação;
- erros externos.

## 17. Ambientes

### Local

Desenvolvedores executam:
- testes rápidos;
- lint;
- type checking;
- testes de integração relevantes.

### Pull Request

CI executa obrigatoriamente os quality gates.

### Main

Após merge:
- suíte completa aplicável;
- build;
- eventual deploy;
- smoke tests, quando implementados.

### Release/produção

Antes ou imediatamente após release:
- smoke tests;
- validações críticas;
- monitoramento de erros.

## 18. Quality Gates do Pull Request

Um PR não deve estar elegível para merge se falhar em checks obrigatórios.

Proposta:

```text
Frontend
[ ] lint
[ ] typecheck
[ ] unit/component tests
[ ] build

Backend
[ ] lint
[ ] typecheck (se adotado)
[ ] unit tests
[ ] integration/API tests

Cross-cutting
[ ] dependency/security checks definidos
[ ] testes E2E críticos quando aplicável
```

Checks mais caros podem ser executados em main ou em eventos específicos, desde que isso não reduza a proteção necessária.

## 19. Rastreabilidade

A estratégia deverá manter relação entre:

```text
Requisito
   |
User Story
   |
Critério de Aceitação
   |
Caso(s) de Teste
   |
Issue / PR
```

Exemplo:

```text
US-03
 |
RF-03
 |
CA-02
 |
TC-SEARCH-001
 |
Issue #...
 |
PR #...
```

Nem todo requisito precisa de um único teste correspondente; um critério pode ser validado por testes automatizados, inspeção, análise estática ou checklist manual.

## 20. Nomenclatura de casos de teste

Para documentação/rastreabilidade, casos importantes poderão usar:

```text
TC-<AREA>-<NNN>
```

Exemplos:
- `TC-SEARCH-001`;
- `TC-PROJECT-001`;
- `TC-I18N-001`;
- `TC-A11Y-001`.

Testes no código não precisam repetir nomenclaturas burocráticas quando nomes comportamentais forem mais claros.

## 21. Definition of Done relacionada à qualidade

Uma feature será considerada pronta quando, conforme aplicável:
- critérios de aceitação forem atendidos;
- testes automatizados necessários forem adicionados;
- suíte existente permanecer aprovada;
- lint/typecheck/build passarem;
- acessibilidade tiver sido considerada;
- estados de erro/loading/empty tiverem sido tratados;
- documentação afetada estiver atualizada;
- code review estiver concluído;
- não houver segredo ou informação sensível introduzida.

## 22. Testes manuais

Testes manuais não deverão substituir testes automatizados repetíveis, mas serão utilizados onde automação não oferecer confiança suficiente.

Checklists manuais serão especialmente relevantes para:
- UX;
- acessibilidade;
- responsividade;
- compatibilidade;
- comportamento de links externos;
- inspeção visual.

## 23. Anti-flakiness

Testes deverão:
- evitar dependência desnecessária de tempo;
- evitar chamadas reais a terceiros na suíte normal;
- controlar dados;
- aguardar estados observáveis em vez de sleeps arbitrários;
- possuir isolamento entre execuções.

Testes flaky devem ser tratados como defeitos da suíte.

## 24. Responsabilidade da equipe

Ambos os desenvolvedores são responsáveis pela qualidade.

Não haverá separação conceitual entre “quem desenvolve” e “quem testa”.

Quem implementa uma alteração deve considerar sua estratégia de validação, e o revisor deve avaliar tanto código quanto testes.

## 25. Critérios de release do MVP

O release do MVP exige:
- requisitos MVP atendidos;
- suíte obrigatória aprovada;
- E2E críticos aprovados;
- ausência de defeitos críticos conhecidos;
- verificação de acessibilidade;
- validação responsiva;
- build reproduzível;
- pipeline verde;
- nenhuma credencial exposta;
- documentação essencial atualizada;
- performance avaliada nas páginas críticas.

## 26. Decisões ainda abertas

Deverão ser escolhidos durante o bootstrap:
- framework de testes frontend;
- biblioteca de testes de componentes;
- ferramenta de mock de rede;
- framework E2E;
- ferramentas de acessibilidade automatizada;
- ferramentas de lint/type checking Python;
- ferramenta de dependency/security scanning;
- execução cross-browser no CI;
- eventual teste de contrato contra GlobalGiving.

As escolhas deverão privilegiar confiabilidade, manutenção e integração com a stack.

## 27. Histórico

| Versão | Status | Descrição |
|---|---|---|
| 0.1 | Draft | Estratégia inicial de testes e qualidade do MVP |
