# Template — CLAUDE.md de módulo

Template do arquivo de contexto que fica dentro de uma pasta de módulo. Alvo: **20-50 linhas**. Se ficar abaixo de ~15 linhas úteis, o módulo provavelmente não justifica um CLAUDE.md próprio — avisar o usuário.

**Regra fundamental:** módulo **nunca** repete stack nem comandos globais. Duplicação vira divergência silenciosa em poucas semanas.

As cercas de quatro crases que delimitam o bloco abaixo são o envelope deste arquivo — não fazem parte do documento gerado. As cercas de três crases dentro dele fazem.

---

````markdown
# Módulo: [Nome do módulo]

<!-- leanwork-context:start -->

## Responsabilidade

[1-2 linhas. O que este módulo faz e onde ele começa e termina. Se você não consegue
descrever a fronteira em duas linhas, o módulo provavelmente está mal delimitado.]

## Domínio

[Entidades, agregados e conceitos principais deste módulo. Lista curta, sem descrever
propriedades — o código é a fonte de verdade para estrutura.]

- **[Agregado raiz]** — [papel em uma linha]
- **[Entidade]** — [papel em uma linha]
- **[Value object relevante]** — [papel em uma linha]

## Boundaries

[O que este módulo pode e não pode acessar. Essencial em arquiteturas modulares como
LMA, onde o enforcement é por disciplina, não por compilador.]

**Pode depender de:**
- [ex.: Módulo `Compartilhado` (tipos base, exceções)]
- [ex.: Módulo `Catalogo` — apenas pela interface pública `ICatalogoPublicApi`]

**Não pode depender de:**
- [ex.: Módulo `Faturamento` — comunicação apenas via evento `PedidoConfirmado`]
- [ex.: Acesso direto às tabelas de outros módulos]

## Convenções locais

[**Apenas** o que diverge do padrão declarado no CLAUDE.md da raiz. Se este módulo
segue exatamente o padrão global, omitir esta seção inteira.]

- [ex.: Este módulo usa Dapper em vez de EF Core para as queries de relatório (ADR-011)]
- [ex.: Handlers deste módulo são idempotentes por contrato — reprocessamento é esperado]

## Comandos específicos

[**Apenas** comandos que só se aplicam a este módulo. Se não houver, omitir a seção.]

```bash
# [ex.: Rodar apenas os testes deste módulo]
[comando real]
```

## Decisões e requisitos aplicáveis

[ADRs e PRDs que afetam especificamente este módulo. Caminhos relativos à raiz.]

- **ADR-002** — [título curto] → `docs/architecture/adrs/ADR-002-*.md`
- **ADR-011** — [título curto] → `docs/architecture/adrs/ADR-011-*.md`
- **PRD-003** — [feature que vive neste módulo] → `docs/prds/PRD-003-*.md`

<!-- leanwork-context:end -->

<!-- Conteúdo abaixo desta linha é mantido manualmente e não é alterado pela skill context-leanwork. -->
````

---

## Notas de preenchimento

### Responsabilidade

Teste de qualidade: se a descrição usa "e também", "além disso" ou lista mais de dois propósitos distintos, o módulo provavelmente tem responsabilidades demais. Vale sinalizar isso ao usuário como observação — pode ser sintoma de boundary mal desenhada, que é assunto para a `architect-leanwork`, não para esta skill.

### Domínio

Listar apenas o que é **conceito de negócio**, não classe de infraestrutura. `Pedido`, `ItemDoPedido`, `StatusPedido` entram; `PedidoRepository`, `PedidoDbContext`, `PedidoMapper` não.

Não descrever propriedades. O código é a fonte de verdade para estrutura de dados; duplicar aqui garante divergência.

### Boundaries

A seção mais valiosa do CLAUDE.md de módulo, especialmente em LMA ou modular monolith. É onde o agente descobre que não pode simplesmente importar a entidade do módulo vizinho.

Extrair da proposta arquitetural (seção 6.3 Componentes, quando existir) e dos ADRs que definem a estratégia de modularização. Se a proposta não define boundaries explicitamente, **perguntar ao usuário** — inventar boundary errada é pior que não ter a seção.

Quando a comunicação inter-módulo é por evento, dizer o nome do evento. O agente precisa saber que a integração é assíncrona.

### Convenções locais

**Omitir a seção inteira se não houver divergência.** Uma seção com "segue o padrão da raiz" é ruído puro.

Toda divergência local deve idealmente ter um ADR por trás. Se o módulo diverge do padrão global sem decisão documentada, isso é um achado — vale reportar ao usuário como observação (pode ser dívida acidental).

### Comandos específicos

Omitir se não houver. Na maioria dos projetos, os comandos são globais e esta seção não existe.

### Decisões e requisitos aplicáveis

Filtrar: apenas ADRs e PRDs que afetam **este** módulo. Um índice completo de todos os ADRs do projeto pertence à raiz, não ao módulo.

Se um módulo tem mais de ~8 ADRs aplicáveis, provavelmente ele é o núcleo do sistema e vale considerar se a modularização está equilibrada.

---

## Quando NÃO criar CLAUDE.md de módulo

Cenários em que a skill deve desaconselhar ativamente:

- **Módulo trivial** — CRUD puro sem regra de negócio, sem boundary especial, sem convenção divergente. O arquivo teria 8 linhas de conteúdo real.
- **Módulo recém-criado sem código** — sem entidades definidas, o Domínio fica vazio e o arquivo nasce desatualizado.
- **Módulo em processo de extração ou fusão** — se a boundary está em movimento, documentar agora gera ruído; esperar estabilizar.
- **Projeto com módulo único** — o CLAUDE.md da raiz já cobre tudo.

Em todos esses casos, informar o motivo ao usuário e deixar a decisão com ele. A skill recomenda, não decide.
