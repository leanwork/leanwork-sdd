# Exemplos de Gherkin — Critérios de Aceite com IDs

Referência de como escrever cenários Gherkin no padrão Leanwork. Os exemplos cobrem padrões comuns: caminho feliz, validação, erro de regra, concorrência, integração externa.

**Convenções:**
- Sintaxe em **português** (`Funcionalidade`, `Cenário`, `Dado`, `E`, `Quando`, `Então`, `Mas`)
- ID `[CA-XX]` entre colchetes no nome do cenário, sempre
- Citação de `RN-XX` entre parênteses ao final do passo, quando o passo valida uma regra
- Citação de `ADR-XX` no nome do cenário, quando a expectativa de comportamento existe por causa de uma decisão arquitetural

---

## Exemplo 1 — Funcionalidade simples com caminho feliz e erro

```gherkin
Funcionalidade: Cadastro de cliente
  Para permitir que novos usuários comprem na loja
  Como visitante anônimo
  Eu quero criar uma conta

  Cenário [CA-01]: Cadastro bem-sucedido com dados válidos
    Dado que estou na tela de cadastro
    E informo nome "Maria Silva"
    E informo e-mail "maria@example.com" válido e não cadastrado (RN-02)
    E informo senha com pelo menos 8 caracteres (RN-03)
    Quando confirmo o cadastro
    Então minha conta é criada com status "ativo"
    E recebo e-mail de boas-vindas
    E sou redirecionada para a tela inicial logada

  Cenário [CA-02]: Tentativa de cadastro com e-mail já existente
    Dado que existe conta cadastrada com e-mail "maria@example.com"
    Quando tento cadastrar nova conta com o mesmo e-mail
    Então o cadastro é rejeitado (RN-02)
    E recebo mensagem "Este e-mail já está em uso"
    E sou orientada a recuperar a senha

  Cenário [CA-03]: Tentativa de cadastro com senha fraca
    Dado que estou na tela de cadastro
    Quando informo senha com menos de 8 caracteres
    Então o cadastro é rejeitado (RN-03)
    E recebo mensagem "Senha precisa ter no mínimo 8 caracteres"
```

---

## Exemplo 2 — Funcionalidade com concorrência

```gherkin
Funcionalidade: Compra em Oferta Relâmpago

  Cenário [CA-04]: Compra com sucesso em oferta ativa
    Dado que existe oferta ativa do produto X com 10 unidades (RN-01)
    E o cliente Y nunca comprou esse produto na oferta atual
    Quando o cliente Y confirma a compra de 1 unidade
    Então o estoque da oferta é decrementado para 9 unidades (RN-05)
    E o pedido é registrado com o preço promocional
    E o cliente recebe confirmação por e-mail

  Cenário [CA-05]: Cliente tenta comprar segunda unidade do mesmo produto
    Dado que o cliente Y já comprou 1 unidade do produto X na oferta atual (RN-03)
    Quando o cliente Y tenta comprar mais 1 unidade
    Então a compra é rejeitada com mensagem "Limite de 1 unidade por cliente nesta oferta"
    E o estoque da oferta não é alterado

  Cenário [CA-06]: Estoque esgota durante compras concorrentes (ADR-002)
    Dado que existe oferta ativa do produto X com 1 unidade restante (RN-05)
    E dois clientes confirmam compra simultaneamente
    Quando o sistema processa as duas requisições
    Então apenas uma compra é confirmada com sucesso
    E a outra é rejeitada com mensagem "Produto esgotado nesta oferta"
    E o estoque final é 0

  Cenário [CA-07]: Tentativa de compra fora da janela de validade
    Dado que existe oferta do produto X com janela "10:00 às 11:00"
    E o horário atual é 11:01
    Quando o cliente tenta confirmar a compra
    Então a compra é rejeitada (RN-01)
    E o produto volta a exibir preço regular
```

---

## Exemplo 3 — Esquema de exemplo (Scenario Outline / Esquema do Cenário)

Use quando o mesmo cenário precisa ser validado com múltiplas combinações de entrada. Evita explosão de cenários idênticos.

```gherkin
Funcionalidade: Cálculo de frete

  Esquema do Cenário [CA-08]: Cálculo de frete baseado em CEP e peso
    Dado que tenho um pedido com peso <peso_kg> kg
    E informo o CEP de destino <cep>
    Quando solicito o cálculo de frete
    Então o valor calculado é R$ <valor_esperado>
    E o prazo de entrega é <prazo_dias> dias

    Exemplos:
      | peso_kg | cep        | valor_esperado | prazo_dias |
      | 1       | 01310-100  | 12.50          | 2          |
      | 1       | 86010-000  | 18.00          | 3          |
      | 5       | 01310-100  | 35.00          | 2          |
      | 10      | 86010-000  | 65.50          | 3          |
```

---

## Exemplo 4 — Integração com sistema externo

```gherkin
Funcionalidade: Sincronização de bula com ANVISA

  Cenário [CA-09]: Sincronização bem-sucedida de bula atualizada
    Dado que existe produto cadastrado com registro ANVISA "1234567890123"
    E o serviço da ANVISA está disponível (RN-08)
    Quando o job diário de sincronização executa
    Então a bula do produto é atualizada com a versão mais recente
    E o campo "ultima_sincronizacao" é registrado com a data/hora atual

  Cenário [CA-10]: Sincronização falha quando serviço externo está fora
    Dado que existe produto cadastrado com registro ANVISA "1234567890123"
    E o serviço da ANVISA retorna erro 503
    Quando o job diário de sincronização executa
    Então a falha é registrada no log estruturado
    E o produto mantém a bula anterior
    E o sistema agenda nova tentativa em 1 hora (RN-09)
    Mas não retentaremos mais de 3 vezes no mesmo dia (RN-10)
```

---

## Exemplo 5 — Comportamento condicional por permissionamento

```gherkin
Funcionalidade: Cancelamento de pedido pelo SAC

  Cenário [CA-11]: Atendente do SAC cancela pedido com motivo válido
    Dado que estou logada como atendente do SAC
    E existe pedido #1234 com status "Pago"
    Quando seleciono o pedido e informo motivo "Solicitação do cliente"
    Então o pedido é cancelado
    E o status muda para "Cancelado pelo SAC"
    E o cliente é notificado por e-mail
    E o estoque do produto é restituído (RN-12)

  Cenário [CA-12]: Cliente comum tenta cancelar pedido
    Dado que estou logada como cliente comum
    E meu pedido #1234 está com status "Pago"
    Quando tento cancelar o pedido na área "Meus Pedidos"
    Então a operação é negada (RN-07)
    E recebo mensagem "Cancelamentos devem ser solicitados ao SAC"
    E é mostrado o telefone do SAC

  Cenário [CA-13]: Atendente sem permissão tenta cancelar pedido de alto valor
    Dado que estou logada como atendente nível 1
    E existe pedido #5678 com valor R$ 5.000 (acima do limite do nível 1)
    Quando tento cancelar o pedido
    Então a operação é bloqueada (RN-13)
    E sou orientada a escalar para supervisor
```

---

## O que evitar

❌ **Cenários sem ID** — sem `[CA-XX]`, o plano não consegue referenciar e a matriz não fecha
❌ **Cenários focados em UI** — Gherkin é sobre comportamento de negócio, não em "clica no botão X". Reservar UI para testes E2E específicos
❌ **Múltiplos comportamentos no mesmo cenário** — "E o estoque é decrementado E o e-mail é enviado E o status muda E..." → quebrar em cenários separados ou aceitar que esse cenário valida múltiplas regras (e marcar todas)
❌ **Mistura de Gherkin com pseudocódigo** — "Dado que `customer.balance = 100`" não é Gherkin de negócio, é detalhe de implementação. Manter linguagem de negócio
❌ **Dependência entre cenários** — cada cenário deve ser independentemente executável. Evitar "Continuando o cenário CA-04..."
❌ **Cenários genéricos demais** — "Cliente compra produto com sucesso" é vago. Ser específico sobre as condições que tornam esse cenário diferente dos outros

## Boas práticas

✅ **Um cenário, uma regra principal** — facilita identificar qual regra está sendo violada quando o teste falha
✅ **`Dado` afirma estado, não ação** — "Dado que existe pedido" e não "Dado que crio um pedido"
✅ **`Quando` afirma uma ação única** — geralmente um único `Quando` por cenário
✅ **`Então` afirma resultado verificável** — "Então o estoque é decrementado" é verificável, "Então o sistema funciona" não é
✅ **Citar `RN-XX` quando o passo é validação de regra** — fecha rastreabilidade
✅ **Citar `ADR-XX` no nome do cenário quando a expectativa depende de decisão arquitetural** — particularmente útil em cenários de concorrência, consistência, falha
✅ **Cobertura mínima por funcionalidade**: caminho feliz + 1-2 variações relevantes + erros prováveis
