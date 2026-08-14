# Catálogo de Estilos Arquiteturais

Referência rápida dos principais estilos arquiteturais com suas forças, fraquezas, isomorfismo de domínio e quando usar (ou evitar). Use durante a Fase 2 (Análise e decisão) para fundamentar a escolha de estilo.

**Princípio guia:** nenhum estilo é "o certo". Cada um é "um certo" para um contexto. A escolha vem do casamento entre domínio, atributos de qualidade prioritários, restrições e capacidade do time — nunca de modismo.

---

## Monolito em camadas (Layered Monolith)

A escolha padrão para a maioria dos projetos. Subestimado por desenvolvedores tentando provar que sabem fazer "coisa moderna".

### Quando usar
- Time pequeno ou médio (1-10 devs)
- Domínio bem conhecido, sem grandes incógnitas
- Volume previsível e escalável verticalmente
- Deploy unificado é aceitável (1 release = 1 unidade)
- Cliente prioriza velocidade de entrega

### Quando evitar
- Múltiplos times grandes que precisam evoluir em paralelo
- Domínios muito distintos com cadências de release diferentes
- Volume já comprovado que exige escala horizontal granular

### Forças
- Simples de entender, desenvolver, debugar
- Transações ACID no banco resolvem maioria dos problemas de consistência
- Deploy simples, rollback simples
- Refactoring intra-projeto é trivial (vs. mover código entre serviços)

### Fraquezas
- Acoplamento se acumula se não houver disciplina de boundaries
- Escalabilidade vertical tem limite físico
- Mudança em uma área pode quebrar outra se camadas vazarem

### Isomorfismo natural
- CRUD com regras de negócio moderadas
- Aplicações administrativas internas
- ERPs verticais
- E-commerce até certo volume

---

## Modular Monolith

Variante disciplinada do monolito: módulos com boundaries explícitas, comunicação por API interna, possibilidade futura de extrair para serviço separado.

### Quando usar
- Mesmas condições do monolito, mas com previsão de crescimento
- Time quer evitar a complexidade operacional de microsserviços mas prepara o terreno
- Múltiplos contextos de negócio razoavelmente independentes
- Saída prudente quando "queremos microsserviços, mas não temos massa crítica ainda"

### Forças
- Boundaries claras forçam disciplina de domínio
- Permite extração futura sem reescrever tudo
- Mantém vantagens operacionais do monolito (deploy simples)
- Facilita aplicação de DDD com bounded contexts

### Fraquezas
- Exige mais disciplina que o monolito ingênuo
- Tooling de enforcement de boundaries é fraco (precisa de PR review rigoroso)
- Pode virar "monolito disfarçado" sem disciplina

### Isomorfismo natural
- E-commerce com módulos de catálogo, pedidos, pagamento, frete
- SaaS multi-tenant com features grandes independentes
- Sistemas internos onde diferentes contextos têm diferentes ritmos de mudança

---

## Microsserviços

Tem sua aplicação, mas é frequentemente mal escolhido por times pequenos perseguindo modernidade ou por arquitetos com viés de complexidade.

### Quando usar
- Múltiplos times independentes (regra de Conway)
- Contextos com cadência de release radicalmente diferentes
- Escala horizontal granular comprovadamente necessária
- Stacks tecnológicas diferentes justificadas (ML em Python + transacional em .NET)
- Time tem maturidade operacional para múltiplos deploys, observabilidade distribuída, transações distribuídas

### Quando evitar
- Time pequeno (< 15 devs)
- Domínio mal compreendido (boundaries vão estar erradas)
- Sem maturidade de DevOps / SRE
- "Queremos escalar" sem volume real ainda
- Sem necessidade comprovada de deploys independentes

### Forças
- Times independentes podem evoluir em paralelo
- Escala granular (escalar só o serviço que precisa)
- Falhas isolam (com circuit breaker)
- Stacks diferentes por contexto

### Fraquezas
- Complexidade operacional grande (orquestração, observabilidade)
- Transações distribuídas via Saga são complexas
- Eventual consistency em todo lugar
- Latência inter-serviço acumula
- Refactoring entre serviços é caro (mover endpoint, mover dado)

### Custo escondido
- Service mesh (Istio, Linkerd)
- Tracing distribuído
- API Gateway
- Schema registry
- Plataforma interna (developer experience)

### Isomorfismo natural
- Empresas grandes com múltiplos times-produto independentes
- Domínios onde cada subdomínio tem requisitos não-funcionais radicalmente diferentes
- Plataformas que precisam atender clientes com SLAs muito distintos

---

## Pipes & Filters

Sequência de transformações bem definida. Cada filtro consome do estágio anterior e produz para o próximo.

### Quando usar
- Processamento sequencial de dados (ETL, processamento de imagem, NLP pipeline)
- Domínio onde cada passo é independente e pode ser desenvolvido isoladamente
- Necessidade de paralelizar etapas
- Reaproveitamento de filtros entre pipelines

### Forças
- Composição flexível (mesmos filtros, diferentes pipelines)
- Testabilidade por filtro
- Paralelização natural
- Cada filtro pode ser uma tecnologia diferente

### Fraquezas
- Overhead se cada filtro for um processo separado
- Difícil tratar erros transversais
- Pipeline reverso (mostrar tudo o que aconteceu) exige observabilidade extra

### Isomorfismo natural
- ETL e data engineering
- Processamento de pedidos linear (validação → reserva → cobrança → fulfillment)
- Pipelines de CI/CD
- Processamento de mídia (vídeo, áudio, imagem)

---

## Event-Driven Architecture (EDA)

Sistema reage a eventos. Produtores publicam, consumidores reagem assincronamente.

### Quando usar
- Sistema reativo a eventos do mundo real (IoT, sensores, fluxos de negócio)
- Necessidade de desacoplar produtores de consumidores
- Múltiplos consumidores interessados no mesmo evento
- Auditoria do que aconteceu é requisito

### Forças
- Acoplamento temporal e estrutural baixo
- Permite adicionar consumidores sem alterar produtor
- Naturalmente assíncrono (resiliência via fila)
- Audit log é subproduto

### Fraquezas
- Difícil rastrear fluxos end-to-end (precisa de tracing)
- Eventual consistency é a norma
- Debugging em produção é mais difícil
- Schema evolution dos eventos é problema crônico (versionamento, contratos)

### Isomorfismo natural
- IoT e sistemas reativos
- E-commerce com múltiplas integrações (pedido confirmado → email, ERP, anti-fraude, logística)
- Sistemas de mensageria interna em organizações grandes

---

## CQRS (Command Query Responsibility Segregation)

Separação entre modelo de escrita e modelo de leitura. Combina bem com Event Sourcing e Event-Driven.

### Quando usar
- Read-heavy radicalmente desproporcional ao write
- Read precisa de projeções otimizadas (denormalização, search, agregações)
- Modelo de domínio na escrita é complexo, mas leitura é simples
- Diferentes consumidores de leitura precisam de formatos diferentes

### Quando evitar
- CRUD simples
- Read e write são equilibrados
- Time não tem maturidade para eventual consistency

### Forças
- Read models otimizados para cada caso de uso
- Escala leitura e escrita independentemente
- Modelo de escrita pode ser rico (DDD), modelo de leitura pode ser bobo (DTO/view)
- Combina naturalmente com cache, search engines, read replicas

### Fraquezas
- Dobra a complexidade (dois modelos para manter)
- Eventual consistency entre comando e leitura
- Debugging é mais complexo (qual model de leitura está desatualizado?)
- Sincronização command → read precisa ser confiável

### Isomorfismo natural
- E-commerce com catálogo muito buscado (search index como read model)
- Dashboards analíticos sobre dados transacionais
- Sistemas com requisitos de busca complexa (Elastic como read model)

---

## Event Sourcing

A fonte de verdade é a sequência de eventos. O estado atual é uma projeção derivada.

### Quando usar
- Auditoria completa é requisito (financeiro, médico, jurídico)
- "Time-travel" é útil (ver estado em qualquer ponto do passado)
- Domínio onde a história do que aconteceu é parte do valor
- Múltiplas projeções diferentes da mesma realidade

### Quando evitar
- CRUD comum
- Time inexperiente (curva de aprendizado é íngreme)
- Não há valor real em auditoria histórica

### Forças
- Audit log perfeito (é a fonte de verdade)
- Pode reconstruir estado em qualquer ponto
- Combina naturalmente com CQRS
- Evolução de modelo de leitura é livre (basta reprocessar eventos)

### Fraquezas
- Complexidade alta
- Migração de eventos antigos é problema crônico (versionamento de eventos)
- Volume de armazenamento alto
- Queries por estado atual são caras sem read models

### Isomorfismo natural
- Sistemas financeiros (cada lançamento é evento)
- Workflow / aprovação (cada transição é evento)
- Auditoria regulatória (saúde, gov)

---

## Microkernel / Plugin Architecture

Core mínimo e plugins que customizam comportamento.

### Quando usar
- Customização heavy por cliente/contexto
- White-label com variações funcionais entre clientes
- IDE-like ou ferramenta extensível
- Necessidade de habilitar/desabilitar features por tenant

### Forças
- Core estável, plugins evoluem independentemente
- Customização sem fork do core
- Permite ecosystem (terceiros podem escrever plugins)

### Fraquezas
- Contrato do plugin é difícil de evoluir
- Debugging cross-plugin é complexo
- Performance pode degradar com muitos plugins ativos

### Isomorfismo natural
- ERPs verticais com customização por cliente
- IDEs (VSCode, JetBrains)
- CMSs (WordPress)
- Plataformas SaaS B2B com tenants muito diferentes entre si

---

## Serverless / FaaS

Funções executadas sob demanda, escalando automaticamente.

### Quando usar
- Carga variável e imprevisível
- Carga média baixa com picos esporádicos
- Glue code entre serviços
- Eventos esparsos (webhook handlers, processamento de upload)
- Custo zero quando idle é importante

### Quando evitar
- Carga sustentada e previsível (custo de FaaS pode ser maior que VM)
- Latência crítica (cold start)
- Funções longas (limites de timeout do provider)
- Necessidade de controle sobre runtime/dependências

### Forças
- Zero ops para o desenvolvedor
- Escala automaticamente até o limite do provider
- Custo proporcional ao uso real
- Excelente para padrões event-driven

### Fraquezas
- Cold start (300ms-3s dependendo do runtime)
- Lock-in com provider de cloud
- Debugging local é mais difícil
- Limites de tempo de execução (15min na maioria)
- Custos podem explodir com má arquitetura

### Isomorfismo natural
- Webhooks
- Processamento de upload (imagem, vídeo)
- Cron jobs
- Integrações ETL leves
- Backend simples de aplicações de baixo volume

---

## REST + API Gateway + Adapters

Integração múltipla com sistemas externos via padronização REST e adapters por integração.

### Quando usar
- Sistema integra com muitos terceiros heterogêneos
- Necessidade de versionamento de API consistente
- Diferentes consumidores precisam de diferentes versões/formatos
- B2B com múltiplos parceiros

### Forças
- Padronização HTTP é amplamente compreendida
- API Gateway centraliza auth, rate limit, logging, versionamento
- Adapters isolam mudanças de terceiros do core

### Fraquezas
- Latência adicional do gateway
- Gateway pode virar gargalo se não for escalado
- Sobrecarga de configuração

### Isomorfismo natural
- Backends para aplicações multi-canal (web, mobile, parceiros)
- Sistemas que expõem API pública para clientes B2B
- Backend-for-Frontend (BFF) pattern

---

## Critério final de escolha

Quando dois estilos parecem se encaixar igualmente, escolha:

1. **O mais simples** que ainda atende os atributos prioritários
2. **O que o time consegue operar** sem precisar contratar/treinar pesadamente
3. **O que tem menor lock-in** dada as restrições do cliente
4. **O que permite evoluir** para o próximo estilo se a hipótese estiver errada

**Lembrete final:** "Boring technology" é uma das melhores escolhas arquiteturais. Postgres, monolito em camadas, e fila simples resolvem 80% dos problemas que microsserviços + Kafka + Event Sourcing prometem resolver — com fração da complexidade operacional.
