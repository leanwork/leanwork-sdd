# Exemplo de Diagrama C4 — Nível 3 (Component), calibrado em .NET

Este é o mesmo exemplo do Nível 3 em `${CLAUDE_PLUGIN_ROOT}/skills/architect-leanwork/references/c4-mermaid-templates.md`, com bibliotecas reais de uma stack .NET (MediatR, FluentValidation, EF Core) no lugar dos nomes de padrão genéricos. Serve para ilustrar como o mesmo diagrama fica quando a stack já está decidida — não é a única forma válida de organizar a camada de aplicação.

> ⚠️ Este exemplo usa Clean/Onion Architecture com MediatR porque é uma combinação comum em projetos .NET, não porque a skill `architect-leanwork` recomenda esse padrão por padrão. A skill lista Clean Architecture entre os modismos a não adotar por moda — ver `SKILL.md`, seção de catálogo de atributos. Trate este diagrama como "assim fica *se* você escolher esse caminho", não como recomendação.

```mermaid
flowchart TB
    subgraph API["API REST (.NET 8)"]
        Controllers["Controllers<br/>(HTTP entry-points)"]
        Mediator["MediatR<br/>(orquestração de handlers)"]

        subgraph Application["Application Layer"]
            Commands["Command Handlers<br/>(escrita)"]
            Queries["Query Handlers<br/>(leitura)"]
            Validators["FluentValidation"]
        end

        subgraph Domain["Domain Layer"]
            Aggregates["Aggregates &<br/>Entities"]
            DomainServices["Domain Services"]
        end

        subgraph Infrastructure["Infrastructure"]
            Repos["Repositories<br/>(EF Core)"]
            ExternalAdapters["External API<br/>Adapters"]
            EventPublisher["Event Publisher<br/>(Service Bus)"]
        end
    end

    DB[("SQL Server")]
    Queue[("Service Bus")]
    Legacy["ERP Legado"]

    Controllers --> Mediator
    Mediator --> Commands
    Mediator --> Queries
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
