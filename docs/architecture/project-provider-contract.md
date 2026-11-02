# Modelos de projetos e contrato de descoberta — Issue #10

O pacote `backend/projects` define conceitos internos do Kindred sem dependências
de FastAPI, HTTP ou GlobalGiving. Implementa a fronteira prevista nos ADR-004 e
ADR-006. Não é um contrato de API pública nem um espelho do JSON externo.

## Dados e ausências

- `ProjectSummary`: ID textual e dados opcionais do card: título, resumo, imagem,
  tema, país e referência da organização.
- `ProjectDetail`: compõe um resumo e acrescenta necessidade, atividades, impacto
  de longo prazo, região e link oficial do projeto. Atividades não são renomeadas
  para uma suposta descrição completa.
- `OrganizationReference`: ID e nome/link opcionais. A referência inteira pode
  estar ausente; não implica carregar uma página de organização.

Somente IDs são obrigatórios. `None` representa informação indisponível, sem
fabricar nomes, imagens, organizações, links ou textos substitutos. Tema e país
são rótulos textuais nesta primeira fronteira; um catálogo com IDs de filtros
poderá ser definido quando necessário. Nenhum ID externo numérico é exigido.
Os modelos são dataclasses imutáveis; a validação e normalização de dados externos,
inclusive URLs, caberão ao futuro adapter antes de criar esses valores internos.

## Provider e continuação

`ProjectProvider` é um `Protocol` assíncrono com duas operações:

- `discover(DiscoveryQuery, Continuation | None) -> DiscoveryResult`: consulta
  sem texto/filtros navega pelo catálogo; texto, tema e país permitem pesquisar.
  `page_size` é positivo e vale 10 por padrão.
- `get_project(id) -> ProjectDetail | None`: retorna `None` para ID inexistente.
  Falhas do provider devem ser propagadas, não convertidas em ausência ou vazio.
  Categorias de erros de integração ficam para a implementação do adapter.

Um resultado contém itens e uma continuação opcional, sem total, número de
páginas ou promessa de um catálogo estável. `None` encerra a navegação dessa
consulta. Não se deve inferir término pelo tamanho do lote nem calcular a
continuação a partir de IDs. O handle pertence à consulta original (incluindo
tamanho de página) e ao provider que o emitiu. A aplicação apenas o devolve.
`start` e `nextProjectId` não fazem parte dessa fronteira. O futuro adapter deve
encapsular seus mecanismos externos e definir validade/duração dos handles;
esta tarefa não implementa armazenamento, cache ou codificação pública deles.
Voltar a páginas já visitadas pode reutilizar resultados/handles guardados pelo
consumidor; navegação por número de página e rotas públicas ficam para outra tarefa.

## Fake e testes

`FakeProjectProvider` recebe detalhes Kindred em memória e satisfaz o protocolo
sem importar qualquer integração. Preserva a ordem de entrada, retorna detalhes
por ID e pagina os resumos. Sua busca faz substring sem distinção de caixa em
título, resumo, tema e nome da organização; filtros de tema e país são comparações
exatas dos rótulos. Essa é uma convenção de teste, não uma garantia sobre campos
indexados pela GlobalGiving. Texto vazio equivale a navegação. Handles opacos são
reutilizáveis durante a vida da instância, vinculados à consulta; handles inválidos
ou de outra instância/consulta geram `ValueError`. A geração do token é aleatória;
os itens e sua ordem são determinísticos. O fake não promete simular falhas de rede.

Os testes unitários cobrem dados completos/parciais, substituição pelo protocolo,
consulta por ID, busca com filtros, vazio, paginação, replay e handles inválidos.
Não há serviço real nem credenciais nos testes.

## Lacuna RF-12 / CA-07

A investigação da [issue #9](globalgiving-capabilities.md) encontrou valores
`funding`, `goal` e `remaining`, mas não confirmou moeda/unidade. Portanto o M1
**não inventa moeda, valores de exibição nem percentual**. Estes modelos não
incluem progresso financeiro. RF-12 e CA-07 permanecem pendentes de confirmação
da semântica e decisão explícita; esta implementação não os declara satisfeitos
nem altera silenciosamente os requisitos.

Ficam fora desta entrega: chamadas GlobalGiving, mappers externos, rotas públicas,
frontend, página de organizações, banco/cache e framework genérico de providers.
