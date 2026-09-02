# Convenções de IDs — Pipeline SDD Leanwork

Este documento é a referência única para os IDs usados pelo pipeline. Todas as seis skills (`architect-leanwork`, `prd-leanwork`, `prototype-leanwork`, `planner-leanwork`, `reviewer-leanwork`, `context-leanwork`) e os comandos que leem artefatos (`/leanwork-trace`, `/leanwork-next`, `/leanwork-execute`, `/leanwork-review`) dependem deste padrão.

## Os seis tipos de ID

| ID | Significado | Onde nasce | Onde é referenciado |
|----|-------------|------------|---------------------|
| `ADR-XX` | Architecture Decision Record | Proposta arquitetural (seção 5) | PRD (regras, citações inline), Plano (campo `Decisões base`), Review (verificação de conformidade) |
| `RN-XX` | Regra de Negócio | PRD (seção 8) | PRD (passos Gherkin entre parênteses), Plano (campo `Implementa`), Review (cobertura por RN) |
| `CA-XX` | Critério de Aceite (cenário Gherkin) | PRD (seção 9, no nome do cenário) | Plano (campo `Valida`), código de teste (nome do teste), Review (cobertura por CA) |
| `UI-XX` | Tela de interface | SPEC-UI (seção 3) | Plano (campo `Telas`), Review (cobertura por UI). Estados usam sufixo: `UI-02.erro` |
| `T-XX` | Tarefa de execução | Plano (cada tarefa numerada) | Outras tarefas (campo `Depende de`), histórico de execução, Review (cada relatório referencia 1 tarefa) |
| `R-XX` | Finding de review (Review-XX) | Relatório de review | Round subsequente de review (referência a findings anteriores), histórico de qualidade |

## Regras de numeração

### Comuns aos seis

- **Numeração sequencial global** ao documento. `T-01`, `T-02`, ..., `T-NN` — **não** reiniciar a numeração por fase ou seção.
- **Largura mínima de 2 dígitos** com zero à esquerda (`RN-01`, `RN-02`, ..., `RN-10`, `RN-11`). Facilita ordenação alfabética e busca em editor.
- **Sem reúso**: uma vez que um ID foi atribuído, ele nunca é reciclado, mesmo que o item original seja revogado. Use marcação de revogação (ver abaixo). **Exceção: `R-XX`** — ver a regra específica adiante.
- **IDs persistem entre versões do documento**. Renumeração quebra o ciclo de rastreabilidade — se você precisar reorganizar, adicione novos IDs no final em vez de renumerar os existentes.

O namespace de um ID é o documento onde ele nasce. Para cinco dos seis tipos isso equivale ao projeto, porque existe um documento de cada — uma proposta arquitetural, um PRD, uma SPEC-UI, um plano. Relatórios de review são muitos: um por tarefa, mais um por round. Por isso `R-XX` é o único ID que se repete dentro do mesmo projeto e o único que precisa ser qualificado ao ser citado.

### Específicas

**ADR-XX**: máximo recomendado de 7-12 ADRs por proposta arquitetural. Se passar disso, provavelmente há decisões triviais entrando na lista — só decisões com trade-off real merecem ADR.

**RN-XX**: cada regra deve ser **verificável**. Se uma regra precisa de mais de um cenário Gherkin para ser provada, considere quebrar em duas regras.

**CA-XX**: aparece dentro do bloco Gherkin como `Cenário [CA-01]: nome do cenário`. Os colchetes são parte da sintaxe — não omitir. Numeração é global ao PRD, não por funcionalidade.

**T-XX**: granularidade calibrada em **30 minutos a 4 horas** de execução — 1 commit ou 1 PR pequeno. Acima de 4 horas, quebrar; abaixo de ~10 minutos, embutir na tarefa vizinha. Tarefa que precisa de mais de 3 critérios de aceite provavelmente é grande demais.

**Este é o teto canônico do pipeline.** `planner-leanwork/SKILL.md` e `planner-leanwork/references/task-examples.md` calibram por ele; nenhum outro número de tamanho de tarefa prevalece sobre este. A faixa é heurística mental para dimensionar a quebra — **não é estimativa e nunca vai escrita no plano**, que registra `Complexidade` qualitativa (`Baixa` / `Média` / `Alta`) e não horas.

**UI-XX**: numeração sequencial global ao documento SPEC-UI. **Estados usam sufixo com ponto** (`UI-02.erro`, `UI-02.vazio`, `UI-02.carregando`), permitindo que o plano declare `Telas: UI-02 (default, erro)` e que o review verifique estado a estado. Tela removida mantém o ID marcado como removido — não reciclar.

**R-XX**: numeração sequencial por relatório (cada `REVIEW-T-XX-*.md` começa do R-01). **Não** numeração global ao projeto. Round subsequente de review da mesma tarefa começa novo relatório com nova numeração; comparar com round anterior pela referência cruzada explícita na seção "Round anterior" do relatório, não pelos IDs.

**Fora do relatório de origem, citar sempre qualificado**: `R-01 (REVIEW-T-04-2026-06-15)`. Vale para o plano, para a matriz de rastreabilidade e para a conversa — "resolvi o R-01" não identifica nada. Qualificar pela tarefa não basta: `R-01 de T-04` continua ambíguo assim que a T-04 tem dois rounds. Quando vários findings do mesmo relatório aparecem juntos, uma qualificação para o grupo resolve: `R-01, R-03 (REVIEW-T-04-2026-06-15)`.

## Vocabulário de status da tarefa

O campo `**Status:**` de cada `T-XX` no plano aceita **exatamente quatro valores**, escritos por extenso e sem emoji:

| Valor | Significado |
|-------|-------------|
| `Pendente` | Ainda não iniciada. Estado inicial de toda tarefa recém-planejada. |
| `Em andamento` | Iniciada e não concluída. |
| `Concluído` | Critérios de aceite atendidos e testes passando. |
| `Bloqueado` | Impedida por dependência, decisão em aberto ou finding Bloqueante de review. |

Transições válidas: `Pendente → Em andamento → Concluído`. De qualquer estado é possível ir para `Bloqueado`, e de `Bloqueado` se volta ao estado anterior quando o impedimento cai.

**Este vocabulário é contrato, não estilo.** `/leanwork-next` e `/leanwork-trace` leem o campo literalmente para descobrir o estado de execução — escrever `Done`, `✅`, `Feito` ou `OK` torna a tarefa invisível para os dois comandos. O plano é a fonte de verdade do estado; um estado que o plano não declara não existe para o pipeline.

### Três eixos de status — não confundir

A palavra "Status" aparece em três lugares do pipeline, com vocabulários próprios. Quem lê os artefatos por busca textual precisa distinguir os três, porque `Concluído` e `Bloqueado` se repetem entre eles:

| Eixo | Onde fica | Valores |
|------|-----------|---------|
| **Documento** | Cabeçalho do plano, do PRD, da SPEC-UI | Plano: `Rascunho` / `Em execução` / `Concluído`. PRD e SPEC-UI: `Rascunho` / `Em revisão` / `Aprovado` |
| **Tarefa** | Campo `**Status:**` dentro do bloco `#### T-XX` | `Pendente` / `Em andamento` / `Concluído` / `Bloqueado` |
| **Review** | Recomendação final do relatório | `Aprovado` / `Aprovado com ressalvas` / `Bloqueado` |

O status de tarefa só é válido **dentro do bloco de uma `T-XX`**. Uma ocorrência de `Status:` antes da primeira tarefa é status de documento e não deve ser lida como estado de execução.

Os emojis (✅ ⚠️ ⛔) permanecem legítimos como decoração de leitura em tabelas de cobertura e na recomendação final do review. No campo `**Status:**` da tarefa, não. Ao citar em prosa, qualificar de qual eixo se fala: `Status: Bloqueado` para a tarefa, `Recomendação: Bloqueado` para o review.

## Marcação de itens revogados

Quando uma decisão ou regra precisa ser revogada (não excluída), use a marcação:

```markdown
### ADR-003: ~~Usar Redis como cache distribuído~~ (revogada por ADR-009)

[manter o conteúdo original como histórico]
```

Isso preserva o ID, mantém a rastreabilidade reversa e documenta a evolução do pensamento.

## Referências cruzadas

### Sintaxe padrão

Sempre que um documento citar um ID de outro documento, use **parênteses inline**:

- No PRD: `RN-05: estoque decrementado atomicamente (ADR-002)` — indica que a regra existe por causa da decisão arquitetural ADR-002
- No Gherkin: `Dado que existe oferta ativa (RN-03)` — indica que o passo valida a regra RN-03
- Na SPEC-UI: `UI-02.limiteExcedido` — estado derivado de `CA-05`, que valida `RN-03`
- No plano (tarefa T-07):
  - `Implementa: RN-03, RN-05` — esta tarefa concretiza essas regras
  - `Valida: CA-01, CA-03` — após essa tarefa, esses cenários ficam verdes
  - `Decisões base: ADR-002` — esta tarefa materializa essa decisão arquitetural
  - `Telas: UI-02 (default, limiteExcedido)` — telas e estados que a tarefa implementa

### Direção das setas

A rastreabilidade flui do macro ao micro:

```
ADR-XX (decisão arquitetural)
   ↓ justifica a existência de
RN-XX (regra de negócio)
   ↓ é provada por
CA-XX (cenário Gherkin)
   ↓ se manifesta em (quando há interface)
UI-XX (tela e estados)
   ↓ é implementada por
T-XX (tarefa de código)
   ↓ é validada por
R-XX (findings do review)
   ↓ é verificada por
Teste_CA-XX_* (no código)
```

Quando o `/leanwork-trace` percorre os artefatos, ele sobe e desce essa cadeia para identificar gaps.

## Convenções de nomenclatura de testes

Para fechar o último elo da cadeia, recomenda-se que testes automatizados carreguem o ID do CA que validam no próprio nome:

```csharp
// xUnit
[Fact]
public void CA_01_Cliente_compra_produto_em_flash_sale_com_sucesso()
{
    // arrange / act / assert
}

[Theory]
[InlineData("CA-02", 0)]
[InlineData("CA-02", -1)]
public void CA_02_Compra_falha_quando_estoque_insuficiente(string ca, int estoque)
{
    // ...
}
```

```typescript
// Jest / Vitest
describe('CA-01 — Cliente compra produto em flash sale com sucesso', () => {
    it('deve persistir pedido e decrementar estoque atomicamente', () => {
        // ...
    });
});
```

Isso permite ao `/leanwork-trace` rodar um grep simples (`grep -r "CA-01" tests/`) e confirmar que o cenário tem cobertura de teste real, não apenas referência teórica no plano.
