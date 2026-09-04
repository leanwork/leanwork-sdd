# Templates Mermaid — C4 Model

Templates prontos para os 4 níveis de C4. Use Mermaid `flowchart` para Context, Container e Component. Use `sequenceDiagram` para fluxos críticos. Nível 4 (Code) raramente compensa — o código já é a fonte de verdade.

## Nível 1 — Context

Mostra o sistema como caixa preta, com pessoas (atores) e sistemas externos com quem ele conversa. Não detalhe o que está dentro.

```mermaid
flowchart TB
    %% Atores
    User[👤 Usuário Final]
    Admin[👤 Administrador]

    %% Sistema sob análise (destaque)
    System["🟦 Sistema X<br/>(sistema sob análise)"]

    %% Sistemas externos
    Legacy["ERP Legado<br/>(SAP)"]
    Email["Provedor de E-mail<br/>(SendGrid)"]
    Pay["Gateway de Pagamento<br/>(Stripe)"]

    User -->|"usa via web/mobile"| System
    Admin -->|"gerencia"| System
    System -->|"consulta produtos e preços"| Legacy
    System -->|"envia transacionais"| Email
    System -->|"processa pagamento"| Pay

    style System fill:#1168bd,color:#fff
```

**Dicas:**
- Destacar o sistema sob análise com cor diferente
- Setas com verbo descritivo, não só linha
- Atores no topo, sistemas externos nas laterais ou embaixo
- Máximo 7±2 elementos para não saturar

## Nível 2 — Container

Mostra as unidades deployáveis dentro do sistema. Cada container é algo que roda separadamente (SPA, API, banco, fila, worker).

```mermaid
flowchart TB
    User[👤 Usuário]

    subgraph System["Sistema X"]
        SPA["SPA<br/>React + Vite"]
        API["API REST<br/>.NET 8"]
        Worker["Worker Assíncrono<br/>.NET 8 Worker Service"]
        DB[("Banco Relacional<br/>SQL Server 2022")]
        Queue[("Fila<br/>Azure Service Bus")]
        Cache[("Cache<br/>Redis 7")]
    end

    Legacy["ERP Legado"]
    Email["SendGrid API"]

    User -->|"HTTPS"| SPA
    SPA -->|"REST/JSON<br/>JWT"| API
    API --> DB
    API -->|"leitura quente"| Cache
    API -->|"publica eventos"| Queue
    Queue -->|"consome"| Worker
    Worker --> DB
    Worker -->|"REST"| Legacy
    Worker -->|"SMTP via API"| Email

    style SPA fill:#08427b,color:#fff
    style API fill:#1168bd,color:#fff
    style Worker fill:#1168bd,color:#fff
```

**Dicas:**
- Cada container ganha tecnologia entre `<br/>` no rótulo
- Bancos e filas com forma de cilindro `[(...)]`
- Setas com protocolo/formato quando relevante
- Sistemas externos fora do `subgraph`

## Nível 3 — Component

Zoom dentro de um container. Use apenas quando faz diferença para a decisão arquitetural. Geralmente só vale para a API ou para o container de domínio mais complexo.

Este exemplo usa nomes de padrão (não de biblioteca) — o objetivo é ilustrar agrupamento lógico, não prescrever uma arquitetura em camadas específica. Para uma versão com bibliotecas reais de uma stack .NET (MediatR, FluentValidation, EF Core), ver `${CLAUDE_PLUGIN_ROOT}/stacks/dotnet/c4-component-example.md`.

```mermaid
flowchart TB
    subgraph API["API REST"]
        Controllers["Entry-points<br/>(HTTP)"]
        Dispatcher["Dispatcher<br/>(orquestração de handlers)"]

        subgraph Application["Application Layer"]
            Commands["Command Handlers<br/>(escrita)"]
            Queries["Query Handlers<br/>(leitura)"]
            Validators["Validadores"]
        end

        subgraph Domain["Domain Layer"]
            Aggregates["Aggregates &<br/>Entities"]
            DomainServices["Domain Services"]
        end

        subgraph Infrastructure["Infrastructure"]
            Repos["Repositories<br/>(acesso a dados)"]
            ExternalAdapters["External API<br/>Adapters"]
            EventPublisher["Event Publisher<br/>(fila/broker)"]
        end
    end

    DB[("Banco Relacional")]
    Queue[("Fila")]
    Legacy["ERP Legado"]

    Controllers --> Dispatcher
    Dispatcher --> Commands
    Dispatcher --> Queries
    Commands --> Validators
    Commands --> Aggregates
    Commands --> Repos
    Commands --> EventPublisher
    Queries --> Repos
    Repos --> DB
    EventPublisher --> Queue
    ExternalAdapters --> Legacy

    style Domain fill:#fff3cd
    style Application fill:#e3f2fd
    style Infrastructure fill:#f8d7da
```

**Dicas:**
- Subgraphs para mostrar agrupamento lógico (camadas, módulos)
- Cores diferentes por camada ajudam a leitura
- Não detalhe classes individuais — é nível 3, não 4
- Este agrupamento em camadas é um exemplo, não uma recomendação — ver catálogo de atributos da skill quanto a quando Clean/Onion Architecture compensa

## Sequence Diagram para fluxos críticos

Use para 1-3 fluxos onde a arquitetura é não-trivial e explicar via diagrama de containers ficaria confuso. Fluxos CRUD óbvios não merecem.

```mermaid
sequenceDiagram
    actor U as Usuário
    participant SPA
    participant API
    participant DB as Banco
    participant Q as Fila
    participant Pay as Gateway Pagto
    participant W as Worker
    participant Mail as E-mail

    U->>SPA: Confirma compra
    SPA->>API: POST /pedidos
    activate API
    API->>Pay: Autoriza cartão
    Pay-->>API: ✅ autorizado (id_transacao)
    API->>DB: BEGIN TX
    API->>DB: INSERT pedido (status=Pago)
    API->>DB: UPDATE estoque
    API->>Q: PUBLISH PedidoConfirmado
    API->>DB: COMMIT
    API-->>SPA: 201 Created (pedido_id)
    deactivate API
    SPA-->>U: Tela de confirmação

    Note over Q,W: Processamento assíncrono

    Q->>W: PedidoConfirmado
    W->>Mail: Envia e-mail de confirmação
    W->>DB: UPDATE pedido (notificado=true)
```

**Dicas:**
- `activate`/`deactivate` para mostrar tempo de execução síncrono
- `Note` para marcar transição síncrono → assíncrono
- Setas tracejadas (`-->>`) para respostas
- Evite mais de 7 participantes — quebra a leitura

## Diagrama de Estados (state diagram) — opcional

Útil quando a arquitetura gira em torno de uma entidade com ciclo de vida não-trivial (pedido, contrato, ticket).

```mermaid
stateDiagram-v2
    [*] --> Rascunho
    Rascunho --> AguardandoPagamento: confirmar
    AguardandoPagamento --> Pago: pagamento_aprovado
    AguardandoPagamento --> Cancelado: pagamento_recusado
    AguardandoPagamento --> Cancelado: timeout_15min
    Pago --> EmSeparacao: separacao_iniciada
    EmSeparacao --> Enviado: nf_emitida
    Enviado --> Entregue: confirmacao_entrega
    Entregue --> [*]
    Cancelado --> [*]

    note right of AguardandoPagamento
        Timeout configurável
        via feature flag
    end note
```

## Anti-padrões comuns

❌ **Diagrama explodido** — mais de 15 elementos no mesmo nível. Quebrar em sub-diagramas ou subir o nível.
❌ **Misturar níveis** — mostrar Container e Component no mesmo diagrama. Confunde.
❌ **Setas sem semântica** — só linhas sem rótulo. Setas devem dizer o que flui (HTTP, eventos, dados).
❌ **Detalhar implementação no Context** — Context é caixa-preta. Tecnologias entram a partir do Container.
❌ **Diagrama que não responde nenhuma pergunta** — se o leitor não consegue tirar uma conclusão arquitetural do diagrama, ele não merece estar na proposta.
