# ADR-002 — React e TypeScript no frontend

## Status

Accepted

## Contexto

O frontend do Kindred deverá oferecer uma aplicação web responsiva e acessível, com busca, filtros, paginação, internacionalização, navegação entre páginas e integração com a Kindred API.

Era necessário escolher uma tecnologia adequada para uma aplicação web pública e que oferecesse bom ecossistema para testes, acessibilidade, internacionalização e manutenção.

Foram consideradas principalmente abordagens baseadas em React/TypeScript e Flutter Web.

## Decisão

Utilizar **React com TypeScript** como base do frontend do Kindred.

O projeto utilizará inicialmente **Vite** como ferramenta de desenvolvimento e build.

Bibliotecas específicas para routing, server state, internacionalização e testes serão avaliadas separadamente e não fazem parte desta decisão, salvo quando se tornarem arquiteturalmente relevantes.

## Alternativas consideradas

### Flutter Web

**Vantagens:**
- experiência consistente entre plataformas;
- possibilidade de compartilhar conhecimento/código com aplicações Flutter futuras;
- modelo de UI integrado.

**Desvantagens:**
- o MVP é prioritariamente uma aplicação web pública baseada em conteúdo e navegação;
- adicionaria uma abordagem menos alinhada ao ecossistema web tradicional;
- poderia aumentar a complexidade para requisitos web específicos.

### React + JavaScript

**Vantagens:**
- ecossistema amplo;
- menor barreira inicial de tipagem.

**Desvantagens:**
- menor segurança estática para contratos e refatorações;
- maior possibilidade de erros detectados apenas em runtime.

### React + TypeScript

**Vantagens:**
- ecossistema consolidado para aplicações web;
- tipagem estática;
- melhor suporte a refatorações;
- contratos mais explícitos entre componentes e API;
- amplo suporte a ferramentas de testes, acessibilidade e i18n.

**Desvantagens:**
- adiciona complexidade de tipos;
- tipos incorretamente modelados podem gerar falsa sensação de segurança;
- exige disciplina para evitar uso excessivo de `any` e abstrações desnecessárias.

## Consequências

### Positivas

- Contratos de dados do frontend poderão ser representados explicitamente.
- Erros de tipo poderão ser detectados antes da execução.
- A equipe terá acesso a um ecossistema amplo para requisitos do MVP.
- Componentização e testes poderão ser desenvolvidos com ferramentas maduras.

### Negativas

- Será necessário configurar e manter toolchain JavaScript/TypeScript.
- Dependências do ecossistema frontend deverão ser controladas para evitar complexidade desnecessária.
- TypeScript não substitui validação de dados recebidos em runtime.

## Notas

Esta decisão não determina a estrutura final de componentes nem todas as bibliotecas do frontend. Essas escolhas devem permanecer proporcionais às necessidades do MVP.
