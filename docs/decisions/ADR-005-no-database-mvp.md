# ADR-005 — Ausência de banco de dados no MVP

## Status

Accepted

## Contexto

O MVP do Kindred possui projetos e organizações provenientes da GlobalGiving e não inclui autenticação, favoritos persistentes, histórico, comentários, pagamentos, analytics próprios ou painel administrativo.

Era necessário decidir se um banco de dados deveria ser incluído desde o início para antecipar funcionalidades futuras.

## Decisão

O MVP **não utilizará banco de dados próprio**.

Dados de projetos e organizações serão obtidos da fonte externa conforme os casos de uso definidos.

Persistência deverá ser introduzida somente quando existir um requisito concreto que a justifique.

## Alternativas consideradas

### PostgreSQL desde o início

**Vantagens:**
- infraestrutura pronta para futuras features;
- possibilidade de persistir/cachar dados;
- demonstra experiência com banco relacional.

**Desvantagens:**
- não existe atualmente dado de domínio que exija persistência própria;
- adiciona migrations, configuração, segurança, backup e operação;
- aumenta complexidade sem atender requisito atual;
- pode criar sincronização desnecessária com a fonte externa.

### Sem banco no MVP

**Vantagens:**
- arquitetura menor;
- menor custo operacional;
- reduz estados e sincronizações;
- mantém foco nos requisitos atuais.

**Desvantagens:**
- funcionalidades futuras que necessitem persistência exigirão mudança arquitetural;
- algumas otimizações baseadas em armazenamento não estarão disponíveis inicialmente.

## Consequências

### Positivas

- Menos infraestrutura para configurar e operar.
- Não haverá modelo persistente sem necessidade.
- A equipe poderá introduzir persistência com base em requisitos reais.

### Negativas

- A aplicação dependerá da fonte externa para os dados do MVP.
- Features como favoritos e contas exigirão nova decisão.
- Uma futura introdução de banco poderá demandar novos componentes e migrations.

## Notas

A ausência de banco não impede cache futuro. Persistência e cache são preocupações diferentes e devem ser justificadas separadamente.

Qualquer introdução de banco de dados deverá resultar em revisão desta decisão ou em novo ADR que a substitua.
