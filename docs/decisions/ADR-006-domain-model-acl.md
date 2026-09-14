# ADR-006 — Modelo de domínio próprio e Anti-Corruption Layer

## Status

Accepted

## Contexto

A GlobalGiving possui seus próprios formatos, nomenclaturas, campos opcionais, mecanismos de paginação e relacionamentos.

Uma alternativa simples seria retornar ao frontend os payloads externos praticamente sem transformação. Isso, porém, faria com que os modelos do Kindred fossem determinados pela estrutura de um serviço de terceiros.

Era necessário definir como os dados externos atravessariam a aplicação.

## Decisão

O Kindred manterá **modelos próprios de domínio e contratos internos**, e a integração com a GlobalGiving funcionará como uma **Anti-Corruption Layer (ACL)**.

A conversão seguirá conceitualmente:

```text
GlobalGiving Response
        |
        v
External Schema
        |
        v
Mapper / Adapter
        |
        v
Kindred Domain Model
        |
        v
API Response
```

Schemas externos permanecerão confinados à camada de integração.

Casos de uso e frontend deverão trabalhar com conceitos e contratos definidos pelo Kindred.

## Alternativas consideradas

### Expor diretamente o payload da GlobalGiving

**Vantagens:**
- menos código de mapeamento;
- implementação inicial mais rápida;
- acesso imediato a todos os campos externos.

**Desvantagens:**
- forte acoplamento;
- mudanças externas propagam-se pelo sistema;
- nomenclaturas externas passam a definir o domínio;
- testes dependem mais de detalhes do provedor;
- tratamento de campos opcionais tende a se espalhar.

### Modelo próprio + ACL

**Vantagens:**
- domínio controlado pelo Kindred;
- menor impacto de mudanças externas;
- contratos internos podem ser mais simples e consistentes;
- facilita testes;
- permite futura integração com outras fontes.

**Desvantagens:**
- exige mappers e modelos adicionais;
- novos campos podem precisar ser propagados explicitamente;
- mapeamentos incorretos tornam-se um risco a ser testado.

## Consequências

### Positivas

- Casos de uso não dependerão dos schemas da GlobalGiving.
- O frontend receberá contratos adequados às necessidades do produto.
- Campos externos poderão ser normalizados.
- Estratégias de paginação externas poderão ser escondidas.
- Uma segunda fonte de dados poderá ser adicionada com menor impacto no domínio.

### Negativas

- A integração terá mais código.
- Alterações legítimas no domínio exigirão atualização de modelos e mappers.
- Testes específicos deverão garantir fidelidade do mapeamento.

## Notas

A ACL não deve transformar o backend em uma abstração excessiva. Somente informações necessárias ao produto deverão ser modeladas.

O objetivo é proteger o domínio, não reproduzir toda a API externa em novos tipos.
