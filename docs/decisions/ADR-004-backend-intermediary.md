# ADR-004 — Backend intermediário entre frontend e GlobalGiving

## Status

Accepted

## Contexto

O Kindred utiliza a GlobalGiving como fonte externa principal. Uma possibilidade seria permitir que o frontend consumisse essa API diretamente.

Entretanto, a integração envolve credenciais e formatos pertencentes a um serviço externo. Além disso, o Kindred precisa tratar falhas, normalizar respostas e manter um contrato próprio para sua interface.

Era necessário decidir entre integração direta frontend → GlobalGiving ou introdução de uma API intermediária do Kindred.

## Decisão

O frontend **não consumirá a GlobalGiving diretamente**.

Toda comunicação relacionada aos dados externos deverá ocorrer através da **Kindred API**:

```text
Frontend
   |
   v
Kindred API
   |
   v
GlobalGiving API
```

A Kindred API será responsável por proteger credenciais, validar parâmetros, adaptar contratos, mapear erros e desacoplar o frontend do provedor.

## Alternativas consideradas

### Frontend → GlobalGiving

**Vantagens:**
- menos um componente para desenvolver e hospedar;
- menor complexidade inicial de infraestrutura.

**Desvantagens:**
- risco de exposição de credenciais;
- forte acoplamento entre UI e API externa;
- tratamento de erros externos espalhado pelo frontend;
- mudanças no provedor impactariam diretamente a aplicação cliente;
- menor controle sobre contratos e futuras estratégias de cache.

### Frontend → Kindred API → GlobalGiving

**Vantagens:**
- credenciais permanecem no servidor;
- contrato interno controlado pelo Kindred;
- integração externa centralizada;
- melhor testabilidade;
- possibilidade futura de cache, observabilidade e outras fontes.

**Desvantagens:**
- adiciona um serviço backend;
- aumenta responsabilidades de deploy e operação;
- introduz um salto adicional de rede.

## Consequências

### Positivas

- O frontend depende do domínio/API do Kindred, não da GlobalGiving.
- Segredos não precisam ser enviados ao navegador.
- Falhas externas podem ser convertidas em respostas consistentes.
- Alterações no provedor podem ser absorvidas pela camada backend.

### Negativas

- A disponibilidade do produto passa a depender também da Kindred API.
- A equipe deverá manter e implantar dois componentes.
- O backend pode se tornar um gargalo se for mal projetado ou operado.

## Notas

O backend não deverá ser um proxy transparente. A adaptação do modelo externo é tratada especificamente no ADR-006.
