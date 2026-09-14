# Kindred — Especificação de Requisitos de Software (SRS)

**Versão:** 0.1  
**Status:** Draft  
**Escopo:** MVP  
**Idioma do documento:** Português  
**Produto:** Kindred  
**Fonte externa principal:** GlobalGiving API

---

## 1. Introdução

### 1.1 Propósito

Este documento especifica os requisitos funcionais e não funcionais do MVP do **Kindred**, uma aplicação web voltada à descoberta de projetos e organizações sociais ao redor do mundo.

O documento tem como objetivo servir como referência para:
- definição do escopo do MVP;
- planejamento do backlog;
- desenho da arquitetura;
- elaboração dos testes;
- criação de critérios de aceitação;
- rastreabilidade entre requisitos, implementação e validação.

### 1.2 Visão do produto

O Kindred é uma plataforma que permite a qualquer pessoa descobrir projetos sociais de acordo com interesses, temas e localização, compreender seus objetivos e impactos e acessar a página oficial do projeto ou organização responsável.

O produto utilizará a GlobalGiving como fonte externa principal de dados.

### 1.3 Objetivos

O MVP deve:

1. permitir a descoberta de projetos sociais;
2. oferecer busca textual e filtros;
3. apresentar informações claras e relevantes sobre cada projeto;
4. apresentar informações sobre a organização responsável;
5. permitir acesso à página oficial do projeto na GlobalGiving;
6. oferecer experiência responsiva, acessível e bilíngue;
7. demonstrar boas práticas de engenharia de software, incluindo requisitos, arquitetura, testes, qualidade, CI/CD, documentação e colaboração.

### 1.4 Público-alvo

O sistema será direcionado a qualquer pessoa interessada em descobrir projetos sociais e organizações beneficentes ao redor do mundo.

### 1.5 Stakeholders

| Stakeholder | Interesse |
|---|---|
| Usuário visitante | Descobrir e compreender projetos sociais |
| Equipe de desenvolvimento | Construir, manter e evoluir o produto |
| GlobalGiving | Fonte externa dos dados utilizados |
| Avaliadores/recrutadores | Avaliar qualidade técnica e práticas de engenharia adotadas |

---

## 2. Escopo do MVP

### 2.1 Funcionalidades incluídas

O MVP será composto pelas seguintes páginas:

- Home;
- Explorar;
- Detalhes do projeto;
- Detalhes da organização.

Também fará parte do MVP:

- busca textual;
- filtros por tema e localização;
- paginação;
- suporte inicial a português e inglês;
- responsividade;
- acessibilidade;
- tratamento de loading, ausência de resultados e erros;
- redirecionamento para páginas oficiais externas;
- integração com a GlobalGiving.

### 2.2 Fora do escopo

Não fazem parte do MVP:

- autenticação;
- cadastro de usuários;
- favoritos persistentes;
- comentários;
- recomendações personalizadas;
- processamento de pagamentos;
- doações dentro do Kindred;
- notificações;
- chat;
- painel administrativo;
- analytics;
- coleta deliberada de dados pessoais;
- sistema próprio de projetos sociais;
- banco de dados persistente, salvo futura necessidade arquitetural devidamente justificada.

---

## 3. Premissas e Restrições

### 3.1 Premissas

**PR-01.** A GlobalGiving será a fonte externa principal de dados do MVP.

**PR-02.** A disponibilidade e completude das informações exibidas dependerão dos dados retornados pela GlobalGiving.

**PR-03.** O sistema poderá exibir somente informações disponibilizadas pela fonte externa ou derivadas diretamente delas.

**PR-04.** O usuário não precisará estar autenticado para utilizar nenhuma funcionalidade do MVP.

### 3.2 Restrições

**RE-01.** O Kindred não deve processar doações ou pagamentos.

**RE-02.** O Kindred não deve armazenar credenciais sensíveis no cliente.

**RE-03.** O MVP não deve depender de um banco de dados próprio sem justificativa arquitetural formal.

**RE-04.** A compatibilidade será direcionada a versões modernas dos principais navegadores, sem garantia de suporte irrestrito a versões antigas.

---

# 4. Requisitos Funcionais

## 4.1 Navegação e apresentação

### RF-01 — Exibir página inicial

O sistema deve disponibilizar uma página inicial que apresente:
- nome e identidade do Kindred;
- propósito da aplicação;
- ação principal para explorar projetos;
- acesso à busca;
- temas/categorias em destaque, quando disponíveis;
- explicação resumida de funcionamento;
- footer com créditos e links relevantes.

### RF-02 — Navegar para a área de exploração

O sistema deve permitir que o usuário acesse a página de exploração a partir da página inicial.

---

## 4.2 Busca e exploração

### RF-03 — Realizar busca textual

O sistema deve permitir que o usuário realize uma busca utilizando texto livre.

A busca poderá utilizar termos relacionados a:
- nome do projeto;
- tema;
- organização;
- conteúdo disponibilizado pela fonte externa, quando suportado.

### RF-04 — Filtrar projetos por tema

O sistema deve permitir a filtragem de projetos por tema ou causa social.

### RF-05 — Filtrar projetos por localização

O sistema deve permitir a filtragem de projetos por país e/ou região, de acordo com os dados disponibilizados pela fonte externa.

### RF-06 — Combinar busca e filtros

O sistema deve permitir o uso simultâneo de busca textual e filtros disponíveis.

### RF-07 — Limpar filtros

O sistema deve permitir que o usuário remova os filtros aplicados e retorne à listagem sem filtros.

### RF-08 — Exibir resultados da busca

O sistema deve exibir os projetos encontrados em uma listagem baseada em cards.

Cada card deve apresentar, quando disponível:
- imagem;
- título;
- tema;
- país ou região;
- resumo curto;
- acesso à página de detalhes.

### RF-09 — Paginar resultados

O sistema deve dividir resultados extensos em páginas.

O usuário deve conseguir:
- avançar;
- voltar;
- identificar a página atual.

---

## 4.3 Detalhes de projeto

### RF-10 — Visualizar detalhes de um projeto

O sistema deve disponibilizar uma página de detalhes para cada projeto selecionado.

### RF-11 — Exibir informações principais do projeto

A página de projeto deve apresentar, quando os dados estiverem disponíveis:
- título;
- imagem;
- tema;
- país ou região;
- resumo;
- necessidade;
- impacto de longo prazo;
- organização responsável.

### RF-12 — Exibir informações financeiras

Quando disponibilizadas pela fonte externa, a página do projeto deve apresentar:
- meta financeira;
- valor arrecadado;
- valor restante;
- progresso percentual.

### RF-13 — Acessar projeto oficial

O sistema deve permitir que o usuário acesse a página oficial do projeto em plataforma externa.

O redirecionamento deve ocorrer de forma explícita, deixando claro que o usuário está deixando o Kindred.

### RF-14 — Acessar organização responsável

O sistema deve permitir que o usuário navegue da página de um projeto para a página da organização responsável.

---

## 4.4 Detalhes da organização

### RF-15 — Visualizar detalhes de uma organização

O sistema deve disponibilizar uma página para exibir informações sobre a organização responsável por um projeto.

### RF-16 — Exibir informações da organização

A página deve apresentar, quando disponíveis:
- nome;
- missão;
- país;
- estado/região;
- países atendidos;
- temas;
- quantidade de projetos.

### RF-17 — Exibir projetos associados

O sistema deve exibir os projetos associados à organização quando a fonte externa disponibilizar essa relação.

### RF-18 — Navegar da organização para um projeto

O usuário deve conseguir acessar a página de detalhes de um projeto listado na página da organização.

---

## 4.5 Internacionalização

### RF-19 — Alternar idioma

O sistema deve oferecer suporte inicial aos idiomas:
- português;
- inglês.

### RF-20 — Persistir preferência de idioma

A preferência de idioma deve ser mantida durante a navegação do usuário na aplicação.

---

## 4.6 Estados de interface

### RF-21 — Exibir estado de carregamento

O sistema deve fornecer feedback visual durante operações assíncronas relevantes.

### RF-22 — Exibir estado sem resultados

Quando uma busca não retornar resultados, o sistema deve informar claramente o usuário e sugerir a alteração dos critérios utilizados.

### RF-23 — Exibir estado de erro

Quando ocorrer falha na comunicação com serviços externos, o sistema deve:
- informar o problema de forma compreensível;
- evitar exposição de detalhes técnicos internos;
- oferecer uma ação de nova tentativa quando aplicável.

---

# 5. Requisitos Não Funcionais

## RNF-01 — Responsividade

A interface deve ser utilizável em:
- desktop;
- tablet;
- dispositivos móveis.

O layout deve se adaptar sem perda de funcionalidade essencial.

## RNF-02 — Acessibilidade

O sistema deve adotar como objetivo de conformidade a **WCAG 2.2 nível AA**.

Devem ser consideradas, entre outras:
- navegação por teclado;
- contraste adequado;
- foco visível;
- textos alternativos para imagens relevantes;
- uso correto de elementos semânticos;
- labels em controles de formulário;
- compatibilidade razoável com tecnologias assistivas.

## RNF-03 — Compatibilidade

O sistema deve ser testado em versões modernas de:
- Google Chrome;
- Mozilla Firefox;
- Microsoft Edge;
- Safari.

Não será exigida compatibilidade irrestrita com navegadores obsoletos.

## RNF-04 — Performance

O sistema deve definir e acompanhar metas objetivas de desempenho utilizando métricas modernas de experiência web.

Durante o desenvolvimento do MVP devem ser monitorados, no mínimo:
- Largest Contentful Paint (LCP);
- Interaction to Next Paint (INP);
- Cumulative Layout Shift (CLS).

Também deve ser utilizado Lighthouse ou ferramenta equivalente como apoio à avaliação de:
- performance;
- acessibilidade;
- boas práticas;
- SEO técnico básico.

As metas quantitativas finais deverão ser registradas na estratégia de qualidade/testes antes do release do MVP.

## RNF-05 — Segurança de credenciais

Credenciais, tokens e chaves privadas não devem ser incluídos no código cliente nem versionados no repositório.

## RNF-06 — Tratamento de falhas externas

Falhas da GlobalGiving não devem provocar comportamento indefinido na interface.

O sistema deve apresentar estados de erro controlados.

## RNF-07 — Qualidade do código

O projeto deve possuir mecanismos automatizados de verificação, incluindo, conforme a stack escolhida:
- lint;
- formatação;
- análise estática;
- testes automatizados;
- build.

## RNF-08 — Integração contínua

Alterações destinadas à branch principal devem passar pelos quality gates definidos no pipeline de CI.

## RNF-09 — Manutenibilidade

O código deve possuir organização modular, nomes claros e separação adequada de responsabilidades.

Decisões arquiteturais relevantes devem ser documentadas.

## RNF-10 — Observabilidade mínima

Erros relevantes da aplicação devem ser registrados de forma adequada para diagnóstico durante desenvolvimento e operação.

A estratégia detalhada será definida posteriormente na documentação de arquitetura/operação.

## RNF-11 — Privacidade

O MVP não deve coletar deliberadamente dados pessoais do usuário.

Não devem ser incluídos analytics, cookies de rastreamento ou tecnologias equivalentes no MVP sem revisão formal do requisito.

## RNF-12 — Disponibilidade dependente de terceiros

A disponibilidade total do sistema poderá ser impactada pela disponibilidade da GlobalGiving.

O Kindred deverá degradar de forma controlada quando o serviço externo estiver indisponível.

---

# 6. Regras de Negócio

## RN-01 — Fonte oficial de dados

Informações de projetos e organizações devem ser derivadas da GlobalGiving ou de outra fonte formalmente aprovada em futura evolução.

## RN-02 — Ausência de processamento de doações

O Kindred deve atuar como plataforma de descoberta.

Doações deverão ocorrer fora do Kindred, utilizando a página oficial disponibilizada pelo serviço externo.

## RN-03 — Dados ausentes

Quando uma informação opcional não estiver disponível, a interface não deve inventar, inferir ou exibir dados incorretos.

O sistema deve omitir o campo ou apresentar estado apropriado.

## RN-04 — Links externos

Links para páginas oficiais externas devem ser claramente identificáveis como navegação externa.

## RN-05 — Projeto como entidade principal

No MVP, a principal entidade de descoberta do Kindred será o **projeto social**.

Organizações serão apresentadas como entidades responsáveis pelos projetos.

---

# 7. User Stories

## US-01 — Conhecer o produto

**Como** visitante,  
**quero** compreender rapidamente o propósito do Kindred,  
**para** decidir se desejo explorar projetos sociais.

## US-02 — Explorar projetos

**Como** visitante,  
**quero** acessar uma área de exploração,  
**para** descobrir projetos disponíveis.

## US-03 — Pesquisar por interesse

**Como** visitante,  
**quero** pesquisar usando termos relacionados aos meus interesses,  
**para** encontrar projetos relevantes.

## US-04 — Filtrar por tema

**Como** visitante,  
**quero** filtrar projetos por causa ou tema,  
**para** encontrar iniciativas alinhadas aos assuntos que me interessam.

## US-05 — Filtrar por localização

**Como** visitante,  
**quero** filtrar projetos por país ou região,  
**para** encontrar iniciativas em localidades específicas.

## US-06 — Navegar entre resultados

**Como** visitante,  
**quero** navegar pelas páginas de resultados,  
**para** analisar mais projetos.

## US-07 — Conhecer um projeto

**Como** visitante,  
**quero** visualizar informações detalhadas sobre um projeto,  
**para** compreender sua finalidade e impacto.

## US-08 — Acompanhar progresso financeiro

**Como** visitante,  
**quero** visualizar o progresso financeiro do projeto quando disponível,  
**para** entender sua situação de arrecadação.

## US-09 — Conhecer a organização

**Como** visitante,  
**quero** acessar informações sobre a organização responsável,  
**para** compreender quem executa o projeto.

## US-10 — Visitar o projeto oficial

**Como** visitante,  
**quero** acessar a página oficial do projeto,  
**para** obter mais informações ou realizar ações externas ao Kindred.

## US-11 — Utilizar o sistema no meu idioma

**Como** visitante,  
**quero** utilizar a aplicação em português ou inglês,  
**para** navegar no idioma de minha preferência.

## US-12 — Utilizar diferentes dispositivos

**Como** visitante,  
**quero** utilizar o Kindred em desktop, tablet ou celular,  
**para** acessar a plataforma no dispositivo disponível.

## US-13 — Utilizar a plataforma com acessibilidade

**Como** usuário com necessidades de acessibilidade,  
**quero** navegar e interagir com os principais recursos usando padrões acessíveis,  
**para** utilizar o produto de forma autônoma.

---

# 8. Critérios de Aceitação

## CA-01 — Home

Relacionado a: **US-01 / RF-01**

- CA-01.1: a página deve exibir o nome Kindred;
- CA-01.2: deve apresentar uma descrição do propósito do produto;
- CA-01.3: deve existir uma ação visível para explorar projetos;
- CA-01.4: deve ser possível acessar a busca;
- CA-01.5: o footer deve apresentar créditos e links definidos para o projeto.

## CA-02 — Busca textual

Relacionado a: **US-03 / RF-03**

- CA-02.1: o usuário deve conseguir informar um termo;
- CA-02.2: a submissão deve iniciar a consulta;
- CA-02.3: deve existir feedback durante o carregamento;
- CA-02.4: resultados compatíveis devem ser exibidos;
- CA-02.5: ausência de resultados deve gerar estado vazio apropriado;
- CA-02.6: falha externa deve gerar estado de erro controlado.

## CA-03 — Filtro por tema

Relacionado a: **US-04 / RF-04**

- CA-03.1: o usuário deve conseguir selecionar um tema;
- CA-03.2: a listagem deve refletir o filtro aplicado;
- CA-03.3: o filtro ativo deve ser identificável;
- CA-03.4: o usuário deve conseguir remover o filtro.

## CA-04 — Filtro por localização

Relacionado a: **US-05 / RF-05**

- CA-04.1: o usuário deve conseguir selecionar localização suportada;
- CA-04.2: os resultados devem respeitar o filtro;
- CA-04.3: o usuário deve conseguir remover o filtro.

## CA-05 — Paginação

Relacionado a: **US-06 / RF-09**

- CA-05.1: resultados extensos devem ser divididos em páginas;
- CA-05.2: o usuário deve conseguir avançar;
- CA-05.3: o usuário deve conseguir voltar;
- CA-05.4: a página atual deve ser identificável;
- CA-05.5: filtros e busca não devem ser perdidos durante a mudança de página.

## CA-06 — Detalhes do projeto

Relacionado a: **US-07 / RF-10 / RF-11**

- CA-06.1: o usuário deve conseguir abrir um projeto;
- CA-06.2: o título deve ser exibido;
- CA-06.3: as informações disponíveis devem ser apresentadas sem preenchimento fictício;
- CA-06.4: a organização responsável deve ser identificável;
- CA-06.5: deve existir navegação para a organização.

## CA-07 — Progresso financeiro

Relacionado a: **US-08 / RF-12**

- CA-07.1: informações financeiras devem ser exibidas somente quando disponíveis;
- CA-07.2: valores exibidos devem ser coerentes com a fonte externa;
- CA-07.3: o progresso percentual deve ser calculado corretamente;
- CA-07.4: ausência de dados financeiros não deve quebrar a interface.

## CA-08 — Organização

Relacionado a: **US-09 / RF-15 / RF-16 / RF-17**

- CA-08.1: o usuário deve conseguir abrir a página da organização;
- CA-08.2: a missão deve ser exibida quando disponível;
- CA-08.3: localização, temas e países atendidos devem ser apresentados quando disponíveis;
- CA-08.4: projetos associados devem ser listados quando disponibilizados pela fonte;
- CA-08.5: deve ser possível acessar os detalhes de um projeto associado.

## CA-09 — Link oficial

Relacionado a: **US-10 / RF-13**

- CA-09.1: deve existir uma ação para acessar o projeto oficial;
- CA-09.2: a ação deve deixar claro que o destino é externo;
- CA-09.3: o Kindred não deve solicitar dados de pagamento.

## CA-10 — Internacionalização

Relacionado a: **US-11 / RF-19 / RF-20**

- CA-10.1: a interface deve estar disponível em português;
- CA-10.2: a interface deve estar disponível em inglês;
- CA-10.3: o usuário deve conseguir alternar entre os idiomas;
- CA-10.4: a preferência deve ser mantida durante a navegação.

## CA-11 — Responsividade

Relacionado a: **US-12 / RNF-01**

- CA-11.1: nenhuma funcionalidade essencial deve ser perdida no mobile;
- CA-11.2: não deve haver rolagem horizontal não intencional;
- CA-11.3: controles devem permanecer utilizáveis em diferentes tamanhos de tela.

## CA-12 — Acessibilidade

Relacionado a: **US-13 / RNF-02**

- CA-12.1: funcionalidades principais devem ser operáveis por teclado;
- CA-12.2: elementos interativos devem possuir foco visível;
- CA-12.3: imagens relevantes devem possuir texto alternativo;
- CA-12.4: inputs devem possuir labels acessíveis;
- CA-12.5: contraste deve atender às metas definidas para WCAG 2.2 AA.

---

# 9. Fluxos Principais

## FL-01 — Descoberta por busca

1. Usuário acessa a Home.
2. Usuário informa um termo.
3. Sistema direciona para Explorar.
4. Sistema consulta os dados.
5. Sistema apresenta resultados.
6. Usuário seleciona um projeto.
7. Sistema apresenta a página de detalhes.
8. Usuário pode acessar a organização ou página oficial externa.

## FL-02 — Descoberta por filtros

1. Usuário acessa Explorar.
2. Usuário seleciona tema e/ou localização.
3. Sistema atualiza a consulta.
4. Sistema apresenta resultados filtrados.
5. Usuário navega entre páginas.
6. Usuário seleciona um projeto.

## FL-03 — Projeto para organização

1. Usuário acessa os detalhes do projeto.
2. Usuário seleciona a organização responsável.
3. Sistema apresenta detalhes da organização.
4. Sistema apresenta seus projetos associados, quando disponíveis.
5. Usuário pode abrir outro projeto.

---

# 10. Estados Excepcionais

## EX-01 — GlobalGiving indisponível

O sistema deve:
1. interromper o estado de carregamento;
2. apresentar mensagem amigável;
3. não exibir stack trace ou detalhes internos;
4. permitir nova tentativa quando aplicável.

## EX-02 — Nenhum resultado encontrado

O sistema deve:
1. informar que nenhum resultado foi encontrado;
2. sugerir alteração da busca ou filtros;
3. oferecer forma simples de limpar filtros.

## EX-03 — Dados incompletos

O sistema deve:
1. exibir os campos disponíveis;
2. omitir ou adaptar campos ausentes;
3. não inventar valores;
4. preservar o restante da interface funcional.

## EX-04 — Projeto inexistente

Quando um identificador não corresponder a um projeto válido, o sistema deve apresentar estado apropriado de recurso não encontrado.

---

# 11. Dependências Externas

## 11.1 GlobalGiving

A GlobalGiving será responsável por fornecer dados relacionados a:
- projetos;
- organizações;
- temas;
- países;
- informações financeiras;
- links externos;
- imagens, quando disponíveis.

A arquitetura deverá considerar:
- disponibilidade da API;
- autenticação;
- limites de requisição;
- formato dos dados;
- tratamento de erros;
- possível cache;
- normalização dos dados.

Esses aspectos serão detalhados no documento de arquitetura.

---

# 12. Matriz de Rastreabilidade Inicial

| User Story | Requisitos relacionados | Critérios |
|---|---|---|
| US-01 | RF-01 | CA-01 |
| US-02 | RF-02 | — |
| US-03 | RF-03, RF-08, RF-21, RF-22, RF-23 | CA-02 |
| US-04 | RF-04, RF-06, RF-07 | CA-03 |
| US-05 | RF-05, RF-06, RF-07 | CA-04 |
| US-06 | RF-09 | CA-05 |
| US-07 | RF-10, RF-11, RF-14 | CA-06 |
| US-08 | RF-12 | CA-07 |
| US-09 | RF-15, RF-16, RF-17, RF-18 | CA-08 |
| US-10 | RF-13 | CA-09 |
| US-11 | RF-19, RF-20 | CA-10 |
| US-12 | RNF-01 | CA-11 |
| US-13 | RNF-02 | CA-12 |

---

# 13. Riscos Iniciais

## RI-01 — Limitações da API externa

A API pode não oferecer todos os filtros, pesquisas ou relacionamentos idealizados.

**Mitigação:** validar capacidades reais antes de consolidar contratos internos.

## RI-02 — Mudanças na API

Alterações no serviço externo podem impactar o Kindred.

**Mitigação:** desacoplar o domínio da aplicação do formato bruto da API.

## RI-03 — Dados incompletos

Projetos podem possuir campos ausentes.

**Mitigação:** modelar campos opcionais e projetar estados de interface adequados.

## RI-04 — Complexidade excessiva do MVP

A introdução prematura de funcionalidades não essenciais pode atrasar a entrega.

**Mitigação:** respeitar a seção “Fora do escopo” e exigir decisão formal para expansão.

## RI-05 — Internacionalização

Português e inglês aumentam a complexidade de interface e testes.

**Mitigação:** tratar i18n como requisito desde o início, evitando textos hardcoded espalhados pelo código.

## RI-06 — Acessibilidade

Conformidade WCAG 2.2 AA exige atenção contínua e não apenas validação ao final.

**Mitigação:** incluir acessibilidade nos critérios de aceitação e na estratégia de testes.

---

# 14. Evoluções Futuras

Possíveis evoluções, fora do MVP:

- autenticação;
- favoritos;
- listas pessoais;
- histórico;
- recomendações;
- múltiplos filtros avançados;
- compartilhamento;
- notificações;
- analytics com revisão de privacidade;
- persistência;
- personalização;
- novos idiomas;
- outras fontes de dados;
- recursos de descoberta assistida.

A inclusão de qualquer item deverá passar por revisão de escopo e atualização deste documento.

---

# 15. Critério de Pronto do MVP

O MVP poderá ser considerado funcionalmente pronto quando:

1. todos os requisitos funcionais classificados como MVP estiverem implementados;
2. critérios de aceitação aplicáveis estiverem atendidos;
3. testes automatizados definidos como obrigatórios estiverem aprovados;
4. pipeline de CI estiver aprovado;
5. páginas essenciais estiverem responsivas;
6. requisitos mínimos de acessibilidade estiverem validados;
7. português e inglês estiverem disponíveis;
8. tratamento de loading, erro e ausência de resultados estiver implementado;
9. documentação técnica essencial estiver atualizada;
10. não houver defeitos críticos conhecidos.

---

# 16. Documentos Relacionados Planejados

Esta especificação deverá ser complementada por:

```text
docs/
├── requirements/
│   └── software-requirements.md
├── architecture/
│   ├── architecture.md
│   └── diagrams/
├── decisions/
│   ├── ADR-001-...
│   ├── ADR-002-...
│   └── ...
├── testing/
│   └── test-strategy.md
└── contributing/
    └── workflow.md
```

Cada documento terá responsabilidade própria:

- **Requirements:** o que o sistema deve fazer;
- **Architecture:** como o sistema será estruturado;
- **ADRs:** por que decisões técnicas importantes foram tomadas;
- **Testing:** como o sistema será validado;
- **Contributing:** como a equipe trabalhará no repositório.

---

# 17. Histórico de Revisões

| Versão | Status | Descrição |
|---|---|---|
| 0.1 | Draft | Primeira especificação do MVP |

