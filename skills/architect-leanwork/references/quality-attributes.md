# Catálogo de Atributos de Qualidade

Referência para a Fase 1 da entrevista (Bloco 2 — Atributos de qualidade prioritários) e para a seção 3 da proposta arquitetural. Use para calibrar perguntas e para mapear cada atributo aos padrões arquiteturais que tipicamente o atendem.

**Princípio guia:** atributo de qualidade só é "prioritário" se houver dor concreta atrelada. Não liste atributos só porque soa profissional. Foque nos 2-4 que **dirigem decisões**.

---

## Performance

### Perguntas-gatilho na entrevista
- Existe expectativa concreta de latência? Para quais operações?
- Há throughput mínimo a sustentar? (req/s, msgs/s, transações/s)
- Há picos previsíveis? (Black Friday, fim de mês, processamento em lote)
- Existe SLA de tempo de resposta documentado?

### Sinais de que é prioritário
- "O usuário desiste se demorar mais de X segundos"
- Cliente B2B com SLA contratual
- Black Friday ou eventos com pico previsto
- Frontend reclama da API constantemente em produção

### Padrões que tipicamente atendem
- Cache (Redis, in-memory) para read-heavy
- Read replicas
- CQRS com read models otimizados
- Materialized views
- CDN para assets e respostas idempotentes
- Async/await + workers para operações longas
- Database tuning (índices, particionamento)

### Trade-offs a explicitar
- vs. **Consistência** (cache + read replicas implicam eventual consistency)
- vs. **Custo** (cache distribuído tem custo de infra)
- vs. **Simplicidade** (CQRS dobra a complexidade de escrita)

---

## Escalabilidade

### Perguntas-gatilho
- A carga vai crescer previsivelmente, exponencialmente, ou é estável?
- Cresce em usuários, em dados, ou em ambos?
- Há projeção concreta de crescimento ou é especulação?
- O crescimento é uniforme ou tem hot-spots?

### Sinais de que é prioritário
- Startup com aquisição agressiva planejada
- Sistema que viraliza eventualmente (mídia, marketing)
- Aplicação multi-tenant onde tenants podem crescer assimetricamente
- Volume atual já gera dor (lentidão, custo crescente)

### Padrões que tipicamente atendem
- Microsserviços (para escalar componentes assimétricos)
- Stateless services + load balancer
- Sharding de banco
- Mensageria para desacoplar produção/consumo
- Auto-scaling (Kubernetes, Container Apps, Lambda)
- Particionamento de dados por tenant/região

### Trade-offs a explicitar
- vs. **Simplicidade operacional** (escala horizontal implica orquestração)
- vs. **Custo de desenvolvimento** (stateless exige mais cuidado)
- vs. **Consistência** (sharding e cache eventual)

### Anti-padrão
- "Vamos com microsserviços porque queremos escalar" sem volume real para justificar — escala horizontal é dívida cobrada antes da hora.

---

## Disponibilidade

### Perguntas-gatilho
- Qual o custo de 1 hora fora do ar? (financeiro, reputacional, contratual)
- Há SLA contratual? Quantos noves?
- Existe janela de manutenção tolerável? (madrugada, domingo)
- O sistema é 24/7 ou tem padrão de uso restrito?

### Sinais de que é prioritário
- B2B com SLA contratual e multa por downtime
- Serviço financeiro ou de saúde com regulação
- E-commerce em horário comercial (ou Black Friday)
- Aplicação crítica para operação interna (downtime = funcionários parados)

### Padrões que tipicamente atendem
- Multi-AZ / multi-região
- Health checks + auto-restart
- Circuit breakers
- Graceful degradation
- Replicação de banco com failover automático
- Blue-green / canary deployments
- Backup + DR (Disaster Recovery) testado periodicamente

### Trade-offs a explicitar
- vs. **Custo** (alta disponibilidade tem custo de infra que cresce não-linearmente)
- vs. **Consistência** (failover pode resultar em split-brain ou perda de dados recentes)
- vs. **Simplicidade** (multi-AZ exige operação madura)

---

## Resiliência

### Perguntas-gatilho
- O sistema pode degradar parcialmente sem cair completamente?
- Há dependências externas críticas? (gateways, APIs de terceiros)
- O que acontece quando uma integração falha? (perda de pedido, fila acumula, etc.)
- Há histórico de incidentes causados por cascata de falhas?

### Sinais de que é prioritário
- Sistema depende de múltiplos serviços externos
- Já teve queda em cascata em produção
- Microsserviços com dependências entre si
- SLA exige funcionar mesmo com algumas funcionalidades indisponíveis

### Padrões que tipicamente atendem
- Circuit breaker (Polly, Resilience4j)
- Retry com exponential backoff
- Timeout explícito em todas as chamadas remotas
- Bulkhead pattern (isolamento de pools)
- Saga pattern para transações distribuídas
- Outbox pattern para eventos confiáveis
- Idempotência em todas as operações de escrita

### Trade-offs a explicitar
- vs. **Simplicidade** (circuit breakers e sagas adicionam complexidade)
- vs. **Performance** (retry e timeout adicionam latência)
- vs. **Consistência** (eventual consistency é a regra em sistemas resilientes)

---

## Segurança

### Perguntas-gatilho
- Lida com dados sensíveis? (financeiros, saúde, PII, segredos comerciais)
- Há requisitos regulatórios? (LGPD, ANVISA, BACEN, PCI DSS, SOC 2)
- Há requisitos de auditoria? (quem viu/alterou o quê e quando)
- Qual o modelo de ameaças? (atacante externo, interno, supply chain)

### Sinais de que é prioritário
- Fintech, healthtech, govtech
- Cliente exige certificação (PCI, ISO 27001, SOC 2)
- Já houve incidente de segurança no projeto ou na empresa
- Dados sensíveis cruzando fronteiras de rede

### Padrões que tipicamente atendem
- Autenticação forte (OAuth2/OIDC, MFA)
- Autorização baseada em policy (não em código espalhado)
- Criptografia em trânsito (TLS) e em repouso (TDE, KMS)
- Secrets management (Azure Key Vault, AWS Secrets Manager)
- Audit log estruturado e imutável
- Threat modeling formal
- Princípio do menor privilégio em IAM
- Validação de entrada em todas as bordas

### Trade-offs a explicitar
- vs. **Disponibilidade** (rate limiting agressivo pode bloquear usuários legítimos)
- vs. **UX** (MFA atrita o login)
- vs. **Performance** (criptografia tem custo)
- vs. **Custo** (compliance tem custo recorrente)

---

## Manutenibilidade

### Perguntas-gatilho
- Frequência de mudança esperada? (alta = código vai mudar muito)
- Time vai crescer? Vai ter muitos contribuidores?
- Há rotatividade no time? (manutenibilidade vira crítica)
- Há código legado que vai conviver com o novo?

### Sinais de que é prioritário
- Produto SaaS com release frequente
- Time crescendo rápido
- Sistema vai ser mantido por anos
- Time atual é júnior e precisa de proteção

### Padrões que tipicamente atendem
- Arquitetura em camadas com fronteiras claras
- Dependency injection
- Cobertura de testes (unit + integration)
- Documentação executável (specs, Gherkin, ADRs)
- Convenções de código aplicadas via linter/formatter
- Modular monolith (boundaries antes de microsserviços)
- DDD para domínios complexos

### Trade-offs a explicitar
- vs. **Time-to-market inicial** (arquitetura boa tem custo upfront)
- vs. **Performance** (camadas adicionam overhead)
- vs. **Simplicidade** (DDD/Clean Architecture é overkill para CRUD simples)

---

## Observabilidade

### Perguntas-gatilho
- Há SRE ou time de operação dedicado?
- O que precisa ser monitorado? (latência, erros, negócio)
- Há requisito de auditoria de quem fez o quê?
- Como bugs são diagnosticados hoje?

### Sinais de que é prioritário
- Sistema distribuído (microsserviços, eventos)
- Operação 24/7 com plantão
- Compliance que exige rastreabilidade
- Histórico de bugs difíceis de reproduzir

### Padrões que tipicamente atendem
- Logging estruturado (JSON, Serilog, etc.)
- Distributed tracing (OpenTelemetry, Application Insights)
- Métricas de negócio + técnicas (Prometheus, Datadog)
- Correlation IDs entre serviços
- Dashboards por contexto de negócio (não só por serviço)
- Alertas baseados em SLO, não em métrica isolada

### Trade-offs a explicitar
- vs. **Custo** (ferramentas de observabilidade têm custo crescente com volume)
- vs. **Performance** (instrumentação tem overhead)
- vs. **Privacidade** (logs podem capturar PII por acidente)

---

## Outros atributos (citar quando relevantes)

- **Portabilidade**: rodar em múltiplas clouds ou on-premise
- **Internacionalização (i18n)**: múltiplos idiomas, fusos, moedas
- **Acessibilidade (a11y)**: conformidade com WCAG, screen readers
- **Custo operacional**: minimizar gasto recorrente de infra
- **Time-to-market**: priorizar entrega rápida sobre tudo
- **Testabilidade**: capacidade de testar componentes isoladamente
- **Reusabilidade**: componentes/serviços que servem múltiplas aplicações

Cada um tem seus padrões e trade-offs próprios — incluir na proposta apenas quando o briefing claramente os exigir.

---

## A regra de ouro

Toda decisão arquitetural na proposta deve poder ser ligada a **pelo menos um atributo de qualidade prioritário** ou a **uma restrição**. Se não consegue ligar, a decisão é gratuita — risco de over-engineering.
