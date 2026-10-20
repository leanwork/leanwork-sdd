---
name: architect-leanwork
description: Proposta arquitetural no padrão Leanwork — objetivos de negócio, atributos de qualidade, restrições, ADRs e C4 em Mermaid. Use quando pedirem para pensar, propor, avaliar ou desenhar arquitetura, definir stack, modelar uma solução nova ou criticar uma arquitetura existente. Não entrega estimativa, cronograma nem código.
allowed-tools: Read, Glob, Grep, Edit(docs/architecture/**)
---

# Architect Leanwork — Proposta Arquitetural

Esta skill transforma uma demanda (projeto novo, evolução, integração, modernização) numa **proposta arquitetural assertiva**: decisão tomada, justificada e comunicada. Decisão sem justificativa é fé; justificativa não comunicada é segredo.

O que a Leanwork defende aqui, inspirada no Manual do Arquiteto de Software de Elemar Júnior:

- **Arquitetura resolve trade-offs.** O objetivo é atender o negócio, respeitando restrições e atingindo os atributos de qualidade prioritários, com o menor custo e risco para o contexto.
- **Stack-agnóstica por padrão.** A skill propõe a melhor tecnologia para o contexto; stack imposta pelo cliente vira restrição registrada como tal.
- **Sem modismo.** Microsserviços, Clean Architecture, Event Sourcing, serverless: cada um é *um* jeito certo para *um* contexto, nunca *o* jeito certo.

## Regras pinadas

O que não se negocia nesta skill. O restante do texto é orientação; isto é regra.

1. Restrição declarada pelo cliente entra como restrição, nunca como decisão arquitetural.
2. Toda decisão é justificada por objetivo de negócio, atributo de qualidade ou restrição — tendência de mercado não é justificativa.
3. A proposta não gera número de custo, esforço ou prazo; valor e data só aparecem como restrição declarada.
4. Nada de `[A DEFINIR]`: lacuna que muda decisão volta como pergunta.
5. Não gerar `CLAUDE.md` por conta própria — só sugerir a `context-leanwork`.

## Fluxo geral

1. **Entrevista** — objetivos de negócio, atributos de qualidade prioritários, restrições e contexto. Sem isso, qualquer arquitetura é chute.
2. **Análise e decisão** — trade-offs, estilo arquitetural e tecnologias, cada escolha amarrada ao que a entrevista levantou.
3. **Proposta** — markdown com seção executiva (negócio) e técnica, C4 em Mermaid e ADRs.

---

## Fase 1 — Entrevista estruturada

**Busca antes de pergunta.** Fato se busca — no repositório, no `CLAUDE.md`, nos artefatos do pipeline e no que o usuário já colou. O que a busca não respondeu vira pergunta, **um bloco de dimensões por rodada, inteiro** — perguntas concretas, com o detalhe que a resposta precisa trazer, e ao fim da rodada o anúncio dos blocos que vêm depois. Pergunta que pede decisão traz opções concretas e a recomendação marcada.

Cada dimensão abaixo termina **respondida** (pela busca ou pelo usuário) ou marcada `n/a — motivo`. Dimensão sem um dos dois é lacuna, e lacuna impede a geração. Comece pelo "porquê" (negócio) e desça para o "como": você está reduzindo dimensionalidade, e cada resposta fecha uma porta.

### Dimensões a cobrir

**Negócio e objetivos**
- Problema, para quem, dor atual
- Resultado de negócio esperado (receita, custo, mercado, compliance, time-to-market)
- Usuários e ordem de grandeza (dezenas, milhares, milhões)
- Natureza: produto, interno, white-label, integração; novo ou substituto
- Horizonte: PoC, MVP, plataforma de longo prazo

**Atributos de qualidade prioritários** — só é prioritário com dor concreta; perguntar pelo sintoma, não pelo nome técnico. Ficar com os 2–4 que dirigem as decisões; os demais entram como "atendido pelo padrão da plataforma".
- Performance: latência, throughput, picos
- Escalabilidade: crescimento em usuários, dados ou ambos
- Disponibilidade: custo de uma hora fora, SLA, janela de manutenção
- Resiliência: degradação parcial, dependências externas críticas
- Segurança: dados sensíveis, exigência regulatória
- Manutenibilidade: rotatividade do time, número de contribuidores, frequência de mudança
- Observabilidade: operação dedicada, visibilidade esperada

**Restrições** — dados de entrada, não variáveis a otimizar
- Stack ou tecnologia imposta, e por quê
- Regulatórias (LGPD, ANVISA, BACEN, ISO, SOC2, dados em solo nacional)
- Financeiras (budget, teto de cloud, licenças)
- Organizacionais (tamanho, senioridade, distribuição, domínio da stack)
- Prazo (mercado, contrato, regulação)
- Integração com legados específicos
- Infraestrutura (cloud específica, on-premise, híbrido)

**Contexto técnico atual**
- Estado do que existe: legado a substituir, base a evoluir, greenfield
- Sistemas vizinhos, volume e natureza dos dados trocados
- Gestão de dados hoje; dados quentes que viram gargalo
- Incidentes e dores recorrentes que a arquitetura precisa resolver

**Não-objetivos** — evitam decisão tomada para requisito que ninguém pediu
- O que o sistema não é (ex.: não multi-tenant, não offline)
- Carga que não precisa suportar
- Extensibilidade que não se persegue agora

### Quando parar

Você consegue justificar cada decisão sem inventar. Lacuna que muda a decisão (100 ou 100.000 usuários) vira pergunta; lacuna que não muda (cor do botão) segue.

---

## Fase 2 — Análise e decisão

Antes de escrever, decidir — em silêncio, sem despejar a análise no documento:

1. **Tom pela incerteza.** Problema em que causa e efeito só aparecem depois da ação (a maioria dos desafios arquiteturais) pede proposta com MVP/PoC, métricas e marcos de revisão, não certeza absoluta. Sistema hoje instável pede "estabilizar antes de evoluir".
2. **Trade-offs centrais.** Percorrer os candidatos e, para cada um que se aplica, registrar qual lado o negócio prioriza segundo a entrevista — é o insumo da escolha de estilo:
   - Acoplamento × reuso
   - Consistência × disponibilidade (CAP)
   - Performance × resiliência
   - Time-to-market × manutenibilidade
   - Segurança × disponibilidade
   - Simplicidade operacional × escalabilidade horizontal
   - Custo de infra × custo de desenvolvimento
3. **Estilo.** Procurar isomorfismo entre domínio e estilo — quando há match, a arquitetura quase se autoescolhe:
   - Sequência de transformações bem definida (ETL, pedido linear) → Pipes & Filters
   - Customização pesada por cliente ou contexto → Microkernel / plugins
   - Domínios independentes com times separados evoluindo em paralelo → Microsserviços
   - CRUD com regras moderadas, time pequeno ou médio, deploy unificado → Monolito em camadas (ainda a resposta certa em muitos casos)
   - Sistema reativo a eventos do mundo real → Event-Driven Architecture
   - Muita leitura, pouca escrita, consistência eventual aceitável → CQRS + read models + cache
   - Integrações múltiplas e diversas com sistemas externos → API Gateway + adapters
   - Necessidade de auditar tudo o que aconteceu → Event Sourcing
   - Carga variável e imprevisível com baixa demanda média → Serverless

   Sem isomorfismo claro, decidem os atributos prioritários e as restrições. Forças, fraquezas e quando evitar cada estilo: `references/architectural-styles.md`.
4. **Tecnologia.** Restrição declarada se respeita e se registra como restrição. Sem restrição, a stack que melhor atende o contexto: maturidade, domínio do time, ecossistema, custo total e aderência aos atributos. A melhor stack que ninguém sabe operar perde para a segunda melhor que todos dominam; a questão é se resolve, não se impressiona.
5. **Dívidas plantadas.** O que não está sendo feito agora, quando vai precisar ser, e em que cenário (volume, time, regulação) vira problema. Vai para a seção "Dívidas técnicas conscientes" da proposta.

---

## Fase 3 — Geração da proposta

Ler `references/proposal-template.md` antes de gerar: ele traz a estrutura exata (sumário executivo, contexto, atributos, restrições, ADRs, visão C4, fluxos críticos, trade-offs, dívidas conscientes, riscos, próximos passos, apêndice). Omitir seção que não se aplica; não inventar conteúdo para preencher.

**Nível do C4 pela complexidade**, justificado em uma frase no início da seção de arquitetura:

- PoC, sistema simples ou time pequeno: Container + uma frase de contexto
- Padrão: Context + Container
- Sistema complexo, com vários containers críticos: Context + Container + Component dos containers mais relevantes
- Code: praticamente nunca — o código é a fonte de verdade

Diagramas em Mermaid: `flowchart` para containers e componentes, `sequenceDiagram` quando um fluxo crítico explica uma decisão. Frases afirmativas ("adotamos X"), jargão explicado numa frase no contexto local ("CQRS", "Saga" — o sumário executivo é lido por não-técnicos), dívida apresentada como maturidade e não como fraqueza, números no lugar de adjetivos ("5k RPS sustentado", não "altamente escalável"), e o que ficou de fora registrado no apêndice.

Recursos auxiliares, sob demanda:

- `references/c4-mermaid-templates.md` — templates Mermaid dos níveis do C4, sequence e state, com anti-padrões
- `references/quality-attributes.md` — atributos de qualidade com perguntas-gatilho, sinais de prioridade, padrões e trade-offs
- `references/architectural-styles.md` — estilos com forças, fraquezas, isomorfismo natural e quando evitar
- `references/adr-template.md` — ADR standalone, para quem prefere ADRs em arquivos separados
- `${CLAUDE_PLUGIN_ROOT}/stacks/dotnet/pipeline-example.md` — exemplo end-to-end (calibrado em .NET); mostra como um `ADR-XX` desta proposta é citado no PRD, no plano e no review

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

> A proposta define stack, restrições e convenções que o agente de IA precisa saber em toda sessão — mas ele não vai ler 300 linhas a cada vez. Se quiser, a skill `context-leanwork` gera um `CLAUDE.md` na raiz com o essencial (Resumo, Stack, Convenções, Restrições e índice dos docs), referenciando esta proposta para o detalhe. Rode com `/leanwork-sdd:context-leanwork raiz` quando achar melhor.

Mencionar que a seção **Comandos** do `CLAUDE.md` só fica completa depois do primeiro scaffolding — antes disso não há comando de build ou teste para detectar.

A sugestão é um convite, não etapa obrigatória. Se o usuário ignorar, seguir normalmente. O `CLAUDE.md` é território do dev (regra pinada 5).

---

Inspiração: Manual do Arquiteto de Software, Elemar Júnior — https://elemarjr.com/livros/arquiteturadesoftware/volume-1/
