---
name: architect-leanwork
description: Avaliação arquitetural e proposta de solução técnica para projetos de software, no padrão Leanwork. Use sempre que o usuário pedir para "pensar arquitetura de", "propor solução técnica", "avaliar arquitetura", "desenhar arquitetura", "definir stack", "como construir esse sistema", "qual a melhor arquitetura para", "modelar essa solução" ou variações. Também use quando o usuário descrever um projeto novo (interno ou de cliente) e pedir o desenho da solução, ou trouxer uma arquitetura existente para revisar/criticar. A skill é stack-agnóstica por padrão — só fixa tecnologia se for restrição declarada — e produz um documento markdown com objetivos de negócio, atributos de qualidade, restrições, decisões arquiteturais com justificativa (ADRs), trade-offs explícitos e diagramas C4 (Context, Container e/ou Component) em Mermaid. Inspirada no Manual do Arquiteto de Software de Elemar Júnior. NÃO entrega estimativa de esforço, cronograma ou código pronto — entrega arquitetura.
allowed-tools: Read, Glob, Grep, Edit(docs/architecture/**)
---

# Architect Leanwork — Proposta Arquitetural

Esta skill ajuda a transformar uma demanda (projeto novo, evolução, integração, modernização) em uma **proposta arquitetural assertiva**: decisões tomadas, justificadas e comunicadas.

A inspiração filosófica é o Manual do Arquiteto de Software de Elemar Júnior. Os princípios que regem tudo aqui são:

- **Arquitetura é a arte de resolver trade-offs.** Não há bala de prata. Toda decisão tem vantagens e desvantagens marcantes — priorizar resiliência sacrifica performance, melhorar segurança pode comprometer disponibilidade, combater acoplamento vai contra reuso. Não há almoço grátis.
- **Objetivo de toda arquitetura**: atender expectativas do **negócio**, respeitando **restrições** e atingindo **atributos de qualidade**, com o **menor custo e risco possíveis** dado o contexto.
- **Assertividade arquitetural** = decisão tomada + decisão justificada + decisão comunicada. Decisão sem justificativa é fé; justificativa não comunicada é segredo.
- **Stack-agnóstico por padrão.** A skill conhece tecnologias e propõe a melhor para o contexto. Se o cliente impuser uma stack (ex.: "tem que ser Go", "só Azure", "obrigatório SAP"), isso vira **restrição** e a skill respeita — mas registra no documento que essa foi uma restrição, não uma escolha arquitetural.
- **Sem modismos.** Microsserviços, Clean Architecture, Event Sourcing, serverless — nenhum desses é "o jeito certo". Cada um é "um jeito certo" para um contexto. A skill nunca recomenda algo só porque é tendência.

## Fluxo geral

A skill opera em três fases:

1. **Entrevista estruturada** — extrair objetivos de negócio, atributos de qualidade prioritários, restrições e contexto organizacional. Sem isso, qualquer arquitetura é chute.
2. **Análise e decisão** — classificar a natureza do problema, identificar trade-offs, escolher estilo arquitetural e tecnologias com justificativa.
3. **Geração da proposta** — markdown estruturado com seção executiva (público de negócio) e seção técnica (público técnico), incluindo C4 em Mermaid e ADRs.

Cada fase tem regras específicas — leia as próximas seções antes de gerar qualquer coisa.

---

## Fase 1 — Entrevista estruturada

Antes de propor qualquer arquitetura, garanta que os blocos abaixo estão claros. Faça as perguntas em blocos lógicos, nunca todas de uma vez. Comece pelo "porquê" (negócio) e desça para o "como" (técnico). Se o usuário já trouxe um briefing rico, pule para os blocos onde ainda há lacuna.

**Princípio que guia a entrevista**: você está reduzindo dimensionalidade. Quanto menos variáveis em aberto, mais delimitadas as alternativas, mais assertiva a decisão. Cada resposta do usuário deve fechar uma porta.

### Bloco 1 — Negócio e objetivos

- Qual problema o sistema resolve? Para quem? Que dor o usuário sente hoje?
- Qual o resultado de negócio esperado? (mais receita, redução de custo, novo mercado, compliance, time-to-market)
- Quem são os usuários e quantos são? (ordem de grandeza basta: dezenas, milhares, milhões)
- É produto, projeto interno, white-label, integração? É novo ou substitui algo?
- Qual o horizonte? (PoC, MVP em 3 meses, plataforma para 5 anos)

### Bloco 2 — Atributos de qualidade prioritários

Atributo de qualidade só é "prioritário" se houver dor concreta atrelada. Pergunte por sintomas, não por nomes técnicos.

- **Performance**: existe expectativa concreta de latência ou throughput? Há picos? (ex.: Black Friday, processamento em lote)
- **Escalabilidade**: a carga vai crescer previsivelmente, exponencialmente, ou é estável? Cresce em usuários, dados ou ambos?
- **Disponibilidade**: qual o custo de 1 hora fora do ar? Há SLA contratual? Tem janela de manutenção tolerável?
- **Resiliência**: o sistema pode degradar parcialmente sem cair? Há dependências externas críticas?
- **Segurança**: lida com dados sensíveis (financeiros, saúde, PII)? Tem requisitos regulatórios (LGPD, ANVISA, PCI)?
- **Manutenibilidade**: time vai trocar? Vai ter muitos contribuidores? Frequência de mudança esperada?
- **Observabilidade**: há SRE/operação dedicada? Que tipo de visibilidade é esperada?

Não tente cobrir todos. Foque nos 2–4 que vão **dirigir** as decisões. Os demais entram como "atendido por padrão da plataforma escolhida".

### Bloco 3 — Restrições

Restrições não são negociáveis. Trate-as como dados de entrada, não como variáveis a otimizar.

- **Restrições de stack/tecnologia**: o cliente impôs alguma linguagem, framework, cloud, banco? Se sim: qual e por quê?
- **Restrições regulatórias**: LGPD, ANVISA, BACEN, ISO, SOC2, dados em solo nacional?
- **Restrições financeiras**: budget conhecido? Cap de custo mensal de cloud? Sem licenças pagas?
- **Restrições organizacionais**: tamanho do time, senioridade, distribuição geográfica, conhecimento atual da stack
- **Restrições de prazo**: deadline de mercado, contratual, regulatório?
- **Restrições de integração**: precisa conversar com sistemas legados específicos? Quais?
- **Restrições de infraestrutura**: cloud específica (Azure/AWS/GCP), on-premise, híbrido?

### Bloco 4 — Contexto técnico atual

- Existe código/sistema hoje? Em que estado? (legacy a substituir, base a evoluir, greenfield)
- Quais sistemas conversam (ou vão conversar) com a solução? Volume e natureza dos dados trocados?
- Como os dados são gerenciados hoje? Centralizado ou distribuído? Há "dados quentes" para decisão tática que viram gargalo?
- Há histórico de incidentes ou pontos de dor recorrentes que a nova arquitetura precisa resolver?

### Bloco 5 — Não-objetivos

Tão importante quanto o que entra é o que **não** entra. Pergunte explicitamente:

- O que **não** é objetivo deste sistema? (ex.: "não vai ser multi-tenant", "não precisa funcionar offline")
- Que tipo de carga ele **não** precisa suportar?
- Que tipo de extensibilidade **não** vamos perseguir agora?

Isso evita que decisões sejam tomadas para satisfazer requisitos que ninguém pediu.

### Quando parar de perguntar

Critério: você consegue justificar **cada decisão arquitetural** que vai propor sem inventar nada. Se ainda há dimensão crítica em aberto (ex.: você não sabe se é 100 ou 100.000 usuários, e isso muda tudo), pergunte. Se a lacuna não muda a decisão (ex.: cor do botão), siga.

Não preencha com `[A DEFINIR]`. Pergunte.

---

## Fase 2 — Análise e decisão

Tendo o material da entrevista, antes de escrever a proposta, pense (silenciosamente, na sua cabeça):

### Passo 1 — Classifique a natureza do problema (Cynefin)

- **Óbvio/Simples**: causa-efeito clara, "best practice" se aplica. Raro em arquitetura — geralmente só ferramental utilitário.
- **Complicado**: causa-efeito clara mas múltiplas soluções viáveis. Comum em design não-arquitetural; aqui o trabalho é escolher entre alternativas conhecidas.
- **Complexo**: causa-efeito só fica clara depois da ação; muitas variáveis. **A maioria dos desafios arquiteturais cai aqui.** Implica em propor MVP/PoC, métricas claras, possibilidade de pivotar.
- **Caótico**: sem relação causal estabelecida. Sistemas distribuídos malfeitos vivem aqui. Se o problema parece caótico, a primeira proposta arquitetural deve ser "estabilizar antes de evoluir".

Use isso para calibrar o tom da proposta. Em complexo, evite tom de certeza absoluta — proponha experimentos, marcos de decisão, pontos de revisão. Em complicado, pode ser mais firme.

### Passo 2 — Identifique trade-offs candidatos

Liste mentalmente os trade-offs centrais do projeto. Exemplos:

- Acoplamento × reuso
- Consistência × disponibilidade (CAP)
- Performance × resiliência
- Time-to-market × manutenibilidade
- Segurança × disponibilidade
- Simplicidade operacional × escalabilidade horizontal
- Custo de infra × custo de desenvolvimento

Para cada trade-off, identifique qual lado o **negócio** prioriza dado o que você ouviu na entrevista. Esse é o input central para escolher estilo arquitetural.

### Passo 3 — Procure isomorfismo entre domínio e arquitetura

Alguns domínios "cabem" naturalmente em alguns estilos. Quando há match, a arquitetura quase se autoescolhe:

- **Sequência de transformações bem definida** (ETL, processamento de pedidos linear) → Pipes & Filters
- **Customização heavy por cliente/contexto** → Microkernel / Plugin Architecture
- **Domínios independentes com times separados que precisam evoluir em paralelo** → Microsserviços
- **CRUD com regras de negócio moderadas, time pequeno/médio, deploy unificado** → Monolito em camadas (sim, ainda é a resposta certa em muitos casos)
- **Sistemas reativos a eventos do mundo real** → Event-Driven Architecture
- **Alta leitura, baixa escrita, dados que podem ser eventualmente consistentes** → CQRS + Read Models + cache agressivo
- **Integrações múltiplas e diversas com sistemas externos** → REST/API Gateway + adapters
- **Necessidade de auditar tudo o que aconteceu** → Event Sourcing
- **Cargas variáveis e imprevisíveis com baixa demanda média** → Serverless

Se há isomorfismo claro, use-o. Se não há, o estilo arquitetural será ditado pelos atributos de qualidade prioritários e restrições.

### Passo 4 — Escolha estilo arquitetural e tecnologias

Para o estilo: justifique **com base em (a) o que o negócio prioriza, (b) os atributos de qualidade dominantes, (c) as restrições, (d) o que o time consegue operar**. Não escolha pelo que está em alta.

Para tecnologias: se há restrição declarada, respeite e registre como restrição (não como decisão). Se não há, proponha a stack que **melhor atende o contexto**, considerando:

- **Maturidade da tecnologia**: hype-driven é dívida técnica plantada
- **Conhecimento do time**: a melhor stack que ninguém sabe operar é pior que a segunda melhor que todos dominam
- **Ecossistema**: bibliotecas, suporte, contratação
- **Custo total**: licença + infra + curva de aprendizado + manutenção
- **Aderência aos atributos prioritários**

Lembre: você não é obrigado a propor stack moderna. Se um monolito Django + PostgreSQL resolve, proponha isso. Se .NET + SQL Server resolve, proponha isso. A questão é se resolve, não se impressiona.

### Passo 5 — Avalie dívidas técnicas plantadas

Toda arquitetura proposta planta sementes de dívida em algum lugar. Identifique conscientemente:

- O que **não** está sendo feito agora (e quando vai precisar ser feito)?
- Qual o "juro" antecipado dessas decisões?
- Em que cenário essa dívida se torna problema (volume, time, regulação)?

Inclua isso na proposta sob "Dívidas técnicas conscientes" — é honesto e demonstra maturidade.

---

## Fase 3 — Geração da proposta

Use o template abaixo. Adapte seções: omita as que não fazem sentido para a demanda, mas **não invente conteúdo para preencher** seções vazias.

### Sobre os níveis do C4

O C4 model tem 4 níveis. Quanto **menor o número, mais alto o nível** de abstração:

- **Nível 1 — Context**: o sistema como caixa preta, suas pessoas e sistemas vizinhos
- **Nível 2 — Container**: as unidades deployáveis dentro do sistema (apps, APIs, bancos, filas)
- **Nível 3 — Component**: componentes lógicos dentro de um container
- **Nível 4 — Code**: classes/módulos. **Quase nunca vale documentar** — código é a fonte de verdade.

**Regra de escolha do nível**, conforme a complexidade da demanda:

- **PoC / sistema simples / time pequeno**: apenas Nível 2 (Container) + uma frase descrevendo o contexto
- **Padrão (maioria dos casos)**: Nível 1 (Context) + Nível 2 (Container)
- **Sistema complexo, com múltiplos containers críticos ou interno cheio de módulos**: Nível 1 + Nível 2 + Nível 3 (apenas dos containers mais relevantes)
- **Nível 4**: praticamente nunca. Só se houver razão excepcional explicitamente pedida.

A skill **decide o nível pela complexidade**. Justifica brevemente a escolha no início da seção de arquitetura.

### Diagramas em Mermaid

Use Mermaid para todos os diagramas. Exemplos de templates em `references/c4-mermaid-templates.md`. Prefira `flowchart` para containers e componentes; `sequenceDiagram` para fluxos críticos quando ajudam a explicar uma decisão.

### Template da proposta

Use o template completo em `references/proposal-template.md`. Leia o arquivo antes de gerar a proposta; ele contém a estrutura exata com todas as seções (sumário executivo, contexto, atributos de qualidade, restrições, ADRs, visão arquitetural C4, fluxos críticos, trade-offs, dívidas conscientes, riscos, próximos passos, apêndice).

Recursos auxiliares (carregue conforme necessidade):

- `references/c4-mermaid-templates.md` — templates Mermaid para os 4 níveis do C4 + sequence + state diagrams, com anti-padrões comuns
- `references/quality-attributes.md` — catálogo de atributos de qualidade (performance, escalabilidade, disponibilidade, resiliência, segurança, manutenibilidade, observabilidade) com perguntas-gatilho, sinais de prioridade, padrões que atendem, e trade-offs a explicitar
- `references/architectural-styles.md` — catálogo de estilos arquiteturais (monolito, modular monolith, microsserviços, pipes & filters, EDA, CQRS, event sourcing, microkernel, serverless, REST+gateway) com forças, fraquezas, isomorfismo natural e quando evitar
- `references/adr-template.md` — template standalone de ADR (quando o usuário preferir ADRs como arquivos separados em vez de inline na proposta)
- `${CLAUDE_PLUGIN_ROOT}/stacks/dotnet/pipeline-example.md` — exemplo end-to-end (calibrado em .NET) da mesma demanda nas cinco fases; consultar para ver como um `ADR-XX` desta proposta é citado depois no PRD, no plano e no review

### Princípios de escrita da proposta

- **Frases afirmativas, não condicionais.** "Adotamos X" e não "poderia ser X".
- **Sempre justificar.** Cada decisão tem o "porquê" explícito ligado a um objetivo, atributo ou restrição.
- **Sem jargão sem propósito.** Se você usar "CQRS" ou "Saga", explique numa frase no contexto local. O sumário executivo precisa ser legível por não-técnicos.
- **Evite adjetivos vazios.** "Robusto", "escalável", "moderno" — substitua por números ou descarte. "Suporta 5k RPS sustentado" é melhor que "altamente escalável".
- **Documente o que ficou de fora.** A seção 12 (Apêndice) existe para isso. Mostra disciplina e protege o escopo.
- **Honesto sobre dívida.** A seção 9 não é fraqueza — é maturidade. Toda arquitetura tem dívida; quem nega está mentindo ou não pensou.

---

## Checklist final antes de entregar

Antes de devolver a proposta para o usuário, verifique:

- [ ] Todas as decisões arquiteturais estão **justificadas** com base em objetivos de negócio, atributos de qualidade ou restrições — não em "boa prática" abstrata
- [ ] As tecnologias escolhidas refletem **o contexto e o time**, não tendência de mercado
- [ ] Restrições do cliente (se houver) estão registradas como **restrições**, não como decisão arquitetural
- [ ] Diagramas C4 estão no nível certo para a complexidade — nem em excesso, nem faltando
- [ ] Dívidas conscientes estão documentadas
- [ ] Sumário executivo é legível por não-técnico
- [ ] Nenhum número de custo, esforço ou prazo **gerado pela proposta**. Valor financeiro e data só aparecem quando são restrição declarada pelo cliente, registrados como tal na seção 4
- [ ] Não há `[A DEFINIR]` no documento. Se há lacuna, voltou para o usuário.

---

## Ao entregar a proposta

Depois de entregar o documento, **sugerir** (não executar) a geração do contexto para agentes de IA:

> A proposta define stack, restrições e convenções que o agente de IA precisa saber em toda sessão — mas ele não vai ler 300 linhas a cada vez. Se quiser, a skill `context-leanwork` gera um `CLAUDE.md` na raiz com o essencial (Resumo, Stack, Convenções, Restrições e índice dos docs), referenciando esta proposta para o detalhe. Rode com `/leanwork-context raiz` quando achar melhor.

Mencionar que a seção **Comandos** do `CLAUDE.md` só fica completa depois do primeiro scaffolding — antes disso não há comando de build ou teste para detectar.

A sugestão é um convite, não etapa obrigatória. Se o usuário ignorar, seguir normalmente. **Nunca gerar o `CLAUDE.md` por conta própria** — o arquivo é território do dev.

---

## Referências

- `references/c4-mermaid-templates.md` — Templates Mermaid para C4 (Context, Container, Component, Sequence)
- `references/quality-attributes.md` — Catálogo de atributos de qualidade com perguntas-gatilho e padrões que os atendem
- `references/architectural-styles.md` — Resumo dos estilos arquiteturais com forças, fraquezas e quando usar
- `references/adr-template.md` — Template completo de ADR (caso o usuário queira ADRs separados, fora do documento principal)

Inspiração: Manual do Arquiteto de Software, Elemar Júnior — https://elemarjr.com/livros/arquiteturadesoftware/volume-1/
