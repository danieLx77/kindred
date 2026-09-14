# Kindred — Workflow de Contribuição

**Versão:** 0.1  
**Status:** Draft  
**Escopo:** Desenvolvimento colaborativo do Kindred

---

## 1. Objetivo

Este documento define o fluxo de trabalho adotado no repositório do **Kindred**.

O objetivo é garantir que alterações sejam:
- rastreáveis;
- revisáveis;
- testadas;
- pequenas o suficiente para facilitar entendimento;
- integradas de forma consistente;
- alinhadas aos requisitos, arquitetura e estratégia de testes do projeto.

O fluxo foi definido considerando uma equipe inicial de dois desenvolvedores, mas deve continuar adequado caso o projeto receba novos colaboradores.

---

# 2. Princípios de colaboração

## PC-01 — Nenhuma alteração relevante diretamente na `main`

A branch `main` representa a versão integrada e estável do projeto.

Alterações relevantes devem ocorrer através de:
1. issue;
2. branch;
3. implementação;
4. testes;
5. Pull Request;
6. CI;
7. code review;
8. merge.

## PC-02 — Mudanças pequenas e focadas

Branches e Pull Requests devem tratar preferencialmente de uma responsabilidade principal.

Evitar PRs que misturem:
- feature;
- refatoração ampla;
- mudança arquitetural;
- correção de bug;
- atualização de documentação sem relação.

## PC-03 — Responsabilidade compartilhada

Não haverá divisão rígida do tipo:

```text
Desenvolvedor A = somente backend
Desenvolvedor B = somente frontend
```

Pode existir ownership principal por tarefa, mas ambos devem participar de:
- revisão;
- decisões;
- integração;
- documentação;
- qualidade.

## PC-04 — Documentação faz parte do produto

Mudanças que afetem:
- comportamento;
- contratos;
- arquitetura;
- decisões;
- requisitos;
- estratégia de testes;

devem atualizar a documentação correspondente quando necessário.

## PC-05 — CI não substitui revisão humana

Automação valida regras objetivas.

Code review deve avaliar também:
- clareza;
- arquitetura;
- manutenibilidade;
- coerência com requisitos;
- complexidade desnecessária;
- experiência do usuário.

---

# 3. Fluxo padrão

O fluxo principal será:

```text
Issue
  ↓
Branch
  ↓
Implementação
  ↓
Testes locais
  ↓
Commit(s)
  ↓
Push
  ↓
Pull Request
  ↓
CI
  ↓
Code Review
  ↓
Ajustes
  ↓
Squash and Merge
  ↓
Delete branch
```

---

# 4. Issues

## 4.1 Objetivo

Issues representam unidades de trabalho rastreáveis.

Podem representar:
- feature;
- bug;
- documentação;
- refatoração;
- tarefa técnica;
- melhoria;
- investigação.

## 4.2 Tamanho

Uma issue deve ser pequena o suficiente para resultar em um PR compreensível.

Evitar:

```text
Implementar frontend inteiro
```

Preferir:

```text
Criar estrutura inicial da página Explore
Implementar ProjectCard
Adicionar endpoint de busca de projetos
Integrar filtros de tema
```

## 4.3 Estrutura recomendada

```md
## Contexto

Por que esta tarefa existe?

## Objetivo

O que deve ser entregue?

## Critérios de aceitação

- [ ] ...
- [ ] ...
- [ ] ...

## Referências

- requisito:
- user story:
- ADR:
- documentação relacionada:
```

## 4.4 Rastreabilidade

Quando aplicável, uma issue deve referenciar:
- requisito funcional;
- requisito não funcional;
- user story;
- critério de aceitação;
- ADR;
- caso de teste.

Exemplo:

```text
US-03
RF-03
CA-02
```

Isso não deve se transformar em burocracia obrigatória para mudanças triviais.

---

# 5. Labels

Uma estrutura inicial de labels pode incluir:

```text
type: feature
type: bug
type: documentation
type: refactor
type: test
type: chore

area: frontend
area: backend
area: architecture
area: devops
area: docs

priority: high
priority: medium
priority: low
```

Labels devem ajudar organização e filtragem, não criar complexidade administrativa.

---

# 6. Branches

## 6.1 Branch principal

```text
main
```

A `main` deve permanecer protegida e sempre em estado integrável.

## 6.2 Criação

Antes de criar uma branch:

```bash
git checkout main
git pull origin main
```

Depois:

```bash
git checkout -b <tipo>/<descricao>
```

## 6.3 Convenção de nomes

Formato:

```text
<tipo>/<descricao-curta>
```

Tipos recomendados:

```text
feature/
fix/
docs/
refactor/
test/
chore/
ci/
```

Exemplos:

```text
feature/project-search
feature/project-details
fix/project-pagination
docs/add-contributing-workflow
refactor/globalgiving-mapper
test/project-search
ci/frontend-quality-gates
```

Usar:
- letras minúsculas;
- palavras separadas por hífen;
- descrição curta;
- sem nomes pessoais.

## 6.4 Issue no nome da branch

O ID da issue pode ser incluído quando for útil:

```text
feature/23-project-search
```

Não será obrigatório inicialmente.

---

# 7. Commits

## 7.1 Conventional Commits

O projeto adotará uma convenção inspirada em **Conventional Commits**.

Formato:

```text
<type>(<scope>): <description>
```

O `scope` é opcional.

## 7.2 Tipos

### feat

Nova funcionalidade.

```text
feat(search): adiciona busca de projetos
```

### fix

Correção de bug.

```text
fix(pagination): corrige navegação para página anterior
```

### docs

Documentação.

```text
docs: adiciona estratégia de testes
```

### refactor

Mudança interna sem alterar comportamento esperado.

```text
refactor(globalgiving): extrai mapper de projetos
```

### test

Adição ou modificação de testes.

```text
test(search): adiciona cenários de busca vazia
```

### chore

Manutenção sem alteração funcional direta.

```text
chore: atualiza dependências de desenvolvimento
```

### ci

CI/CD.

```text
ci: adiciona pipeline do backend
```

### build

Mudanças no sistema de build ou dependências de produção.

```text
build(frontend): configura vite
```

### perf

Melhoria de performance.

```text
perf(projects): reduz chamadas redundantes
```

## 7.3 Idioma

As mensagens de commit serão escritas em **inglês**, mantendo os tipos do Conventional Commits.

Exemplo:

```text
feat(project): add page details
```

## 7.4 Regras

A descrição deve:
- iniciar com verbo;
- ser objetiva;
- evitar ponto final;
- representar a intenção da alteração.

Preferir:

```text
fix(search): trata resposta vazia da API
```

Evitar:

```text
fix
ajustes
mudanças
commit final
corrigindo coisas
```

## 7.5 Frequência

Commits devem representar unidades lógicas de mudança.

Não é necessário criar um commit para cada arquivo.

Também não é necessário preservar commits intermediários desorganizados na `main`, pois será utilizado squash merge.

---

# 8. Pull Requests

## 8.1 Regra geral

Toda alteração relevante deve chegar à `main` por Pull Request.

## 8.2 Título

O título do PR deve seguir padrão semelhante aos commits:

```text
feat(search): adiciona busca e filtros iniciais
```

Como o projeto utilizará squash merge, esse título poderá se tornar a mensagem final do commit na `main`.

## 8.3 Descrição recomendada

```md
## O que foi feito

- ...
- ...

## Por que

...

## Como testar

1. ...
2. ...
3. ...

## Evidências

Screenshots, logs ou resultados quando aplicável.

## Checklist

- [ ] Testes adicionados/atualizados
- [ ] Testes locais aprovados
- [ ] Documentação atualizada
- [ ] Acessibilidade considerada
- [ ] Não introduz segredos
- [ ] Critérios de aceitação atendidos

Closes #...
```

## 8.4 Vinculação com issue

Quando o PR concluir uma issue:

```text
Closes #23
```

ou equivalente.

Isso permite que o GitHub feche a issue automaticamente após o merge.

---

# 9. Code Review

## 9.1 Revisão cruzada

Sempre que possível, um desenvolvedor não deve aprovar e integrar sozinho sua própria alteração sem revisão do outro.

Fluxo:

```text
Autor
  ↓
Pull Request
  ↓
Outro desenvolvedor revisa
  ↓
Aprovação ou solicitação de mudanças
```

## 9.2 O que revisar

### Correção

- atende ao objetivo da issue?
- critérios de aceitação estão satisfeitos?
- existem casos de borda relevantes?

### Arquitetura

- respeita as fronteiras definidas?
- introduz acoplamento desnecessário?
- contraria algum ADR?
- está adicionando tecnologia sem necessidade?

### Código

- nomes são claros?
- responsabilidades estão bem separadas?
- existe duplicação relevante?
- código está mais complexo que o necessário?

### Testes

- comportamento importante foi testado?
- teste verifica comportamento real?
- existe dependência desnecessária de serviço externo?
- regressões estão protegidas?

### Segurança

- algum segredo foi introduzido?
- dados externos são validados?
- logs podem expor informação sensível?

### Frontend

- loading, erro e empty state foram considerados?
- responsividade foi afetada?
- acessibilidade foi considerada?
- textos estão preparados para i18n?

### Documentação

- requisitos ou arquitetura foram alterados?
- é necessário novo ADR?
- README ou documentação precisam ser atualizados?

---

# 10. Comentários de review

Comentários devem ser claros e construtivos.

Quando útil, pode-se diferenciar severidade:

```text
blocking:
suggestion:
question:
nit:
```

### blocking

Problema que deve ser resolvido antes do merge.

```text
blocking: esta chave está sendo enviada para o frontend.
```

### suggestion

Melhoria recomendada, mas não necessariamente bloqueante.

```text
suggestion: podemos extrair essa transformação para o mapper.
```

### question

Pedido de contexto ou justificativa.

```text
question: existe motivo para essa chamada ocorrer duas vezes?
```

### nit

Detalhe pequeno de estilo.

```text
nit: este nome poderia ser mais descritivo.
```

O objetivo do review é melhorar o produto e compartilhar conhecimento, não demonstrar superioridade técnica.

---

# 11. CI

Todo Pull Request deverá passar pelos checks obrigatórios definidos na estratégia de testes.

Conceitualmente:

```text
Pull Request
      |
 +----+----+
 |         |
Frontend Backend
 |         |
lint      lint
types     types
tests     tests
build     integration
 |         |
 +----+----+
      |
      v
Eligible for merge
```

Falha em check obrigatório bloqueia o merge.

Checks adicionais poderão ser adicionados conforme o projeto evoluir.

---

# 12. Proteção da `main`

Configuração recomendada no GitHub:

- exigir Pull Request antes do merge;
- exigir pelo menos 1 aprovação;
- exigir aprovação dos status checks;
- impedir merge com CI falhando;
- exigir branch atualizada quando necessário;
- impedir force push;
- impedir exclusão da `main`.

Como a equipe possui apenas dois integrantes, regras excessivamente rígidas devem ser evitadas se bloquearem manutenção legítima.

---

# 13. Estratégia de merge

O Kindred utilizará **Squash and Merge**.

Exemplo de commits em uma branch:

```text
feat(search): cria formulário
test(search): adiciona teste
fix(search): corrige paginação
refactor(search): simplifica estado
```

Após o merge:

```text
feat(search): adiciona busca e filtros de projetos
```

Benefícios:
- histórico da `main` mais limpo;
- um commit por PR;
- facilita reversão;
- permite commits intermediários durante desenvolvimento.

---

# 14. Exclusão da branch

Após merge:

```bash
git checkout main
git pull origin main
git branch -d nome-da-branch
```

A branch remota deverá ser removida após integração, preferencialmente utilizando o botão **Delete branch** do GitHub.

---

# 15. Definition of Ready

Antes de iniciar uma tarefa, idealmente devem estar claros:

- objetivo;
- contexto;
- critérios de aceitação principais;
- dependências conhecidas;
- requisito relacionado, quando houver.

Nem toda tarefa trivial precisa de formalização completa.

---

# 16. Definition of Done

Uma alteração será considerada concluída quando, conforme aplicável:

- [ ] objetivo da issue foi atendido;
- [ ] critérios de aceitação foram satisfeitos;
- [ ] testes necessários foram adicionados/atualizados;
- [ ] suíte obrigatória está verde;
- [ ] lint/typecheck/build estão aprovados;
- [ ] estados de loading, erro e vazio foram considerados;
- [ ] acessibilidade foi considerada;
- [ ] responsividade foi considerada;
- [ ] segurança foi considerada;
- [ ] documentação afetada foi atualizada;
- [ ] não há segredo versionado;
- [ ] code review foi concluído;
- [ ] CI está aprovado;
- [ ] PR foi integrado via squash merge.

---

# 17. Mudanças arquiteturais

Uma alteração deve considerar um novo ADR quando:

- introduzir tecnologia estrutural;
- alterar fronteiras entre componentes;
- introduzir banco, fila ou cache distribuído;
- mudar protocolo entre frontend e backend;
- substituir framework principal;
- introduzir nova fonte de dados;
- alterar estratégia de deploy de forma significativa.

Fluxo:

```text
Problema
   ↓
Discussão
   ↓
ADR proposto
   ↓
Review
   ↓
Accepted
   ↓
Implementação
```

Mudanças pequenas de biblioteca não exigem necessariamente ADR.

---

# 18. Mudanças nos requisitos

Caso a implementação revele que um requisito precisa mudar:

1. não modificar silenciosamente o comportamento;
2. discutir a mudança;
3. atualizar `software-requirements.md`;
4. atualizar critérios de aceitação;
5. atualizar testes afetados;
6. criar ADR se houver impacto arquitetural significativo.

---

# 19. Bugs

Ao identificar um bug:

1. criar issue quando a correção não for trivial/imediata;
2. registrar comportamento esperado e atual;
3. reproduzir;
4. corrigir;
5. adicionar teste de regressão quando viável;
6. abrir PR normalmente.

Exemplo de issue:

```md
## Comportamento atual

Ao navegar para a próxima página, o filtro de país é perdido.

## Comportamento esperado

O filtro deve permanecer aplicado.

## Passos para reproduzir

1. ...
2. ...
3. ...
```

---

# 20. Hotfixes

Como o MVP ainda não possui operação crítica, não será adotado inicialmente um fluxo específico de hotfix.

Correções urgentes seguem:

```text
main
 ↓
fix/...
 ↓
PR
 ↓
review + CI
 ↓
merge
```

A proteção da branch não deve ser ignorada por conveniência.

---

# 21. Dependabot e dependências

Atualizações automáticas poderão ser utilizadas.

PRs de dependências devem ser avaliados como qualquer alteração:

- verificar changelog relevante;
- avaliar breaking changes;
- executar CI;
- evitar merge automático de mudanças de alto risco sem análise.

Dependências de desenvolvimento poderão futuramente ser agrupadas quando isso reduzir ruído.

---

# 22. Trabalho em paralelo

Antes de iniciar uma issue, os desenvolvedores devem evitar duplicação de esforço.

Pode-se utilizar:
- assignee;
- status no projeto;
- comentário informando início;
- comunicação direta.

Branches devem partir da versão atualizada da `main`.

---

# 23. Conflitos

Em caso de conflito:

1. atualizar `main`;
2. integrar/rebasear conforme estratégia definida pela equipe;
3. resolver conscientemente;
4. executar novamente os testes;
5. nunca aceitar automaticamente ambos os lados sem entender o resultado.

A equipe poderá padronizar merge ou rebase para atualização de branches posteriormente.

---

# 24. Commits e segredos

Antes de qualquer commit, verificar que não estão sendo adicionados:

```text
.env
API keys
tokens
credentials
certificados privados
```

Arquivos de exemplo deverão utilizar:

```text
.env.example
```

sem valores reais.

Caso um segredo seja commitado, removê-lo do arquivo não é suficiente: a credencial deve ser considerada comprometida e rotacionada.

---

# 25. Comandos de referência

Fluxo normal:

```bash
git checkout main
git pull origin main

git checkout -b feature/nome-da-feature

# desenvolvimento

git status
git add .
git commit -m "feat(scope): descrição"

git push -u origin feature/nome-da-feature
```

Depois:
1. abrir Pull Request;
2. aguardar CI;
3. receber review;
4. realizar ajustes;
5. squash and merge;
6. excluir branch.

Atualização após merge:

```bash
git checkout main
git pull origin main
git branch -d feature/nome-da-feature
```

---

# 26. Exemplo completo

Issue:

```text
#23 — Implementar busca de projetos
```

Branch:

```text
feature/23-project-search
```

Commits locais:

```text
feat(search): adiciona formulário de busca
feat(api): integra endpoint de projetos
test(search): adiciona cenários de busca
```

PR:

```text
feat(search): adiciona busca de projetos
```

Descrição:

```text
Closes #23

Atende:
- US-03
- RF-03
- CA-02
```

Após aprovação:

```text
Squash and Merge
```

Resultado na `main`:

```text
feat(search): adiciona busca de projetos
```

---

# 27. Evolução do workflow

Este workflow deverá evoluir com o projeto.

Mudanças podem ser necessárias caso:
- equipe cresça;
- múltiplos ambientes sejam adicionados;
- releases formais sejam adotados;
- versionamento semântico seja introduzido;
- deployments tornem-se mais complexos;
- o projeto aceite contribuições externas.

O processo deve apoiar a engenharia, não se tornar um fim em si mesmo.

---

# 28. Histórico

| Versão | Status | Descrição |
|---|---|---|
| 0.1 | Draft | Workflow inicial de colaboração e contribuição |
