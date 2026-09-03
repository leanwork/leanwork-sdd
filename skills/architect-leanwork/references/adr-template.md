# Template — Architecture Decision Record (ADR)

Use este template quando o usuário pedir ADRs como arquivos separados (`docs/architecture/adrs/ADR-XXX-titulo.md`) em vez de inline na proposta arquitetural.

Para projetos pequenos e médios, ADRs inline (seção 5 da proposta) bastam. Para projetos com decisões evolutivas frequentes ou times grandes, arquivos separados versionam melhor.

As cercas de quatro crases que delimitam o bloco abaixo são o envelope deste arquivo — não fazem parte do documento gerado. As cercas de três crases dentro dele fazem.

---

````markdown
# ADR-XXX: [Título curto e descritivo, em modo imperativo]

> **Status:** [Proposta | Aceita | Revogada | Substituída por ADR-YYY]
> **Data:** [AAAA-MM-DD]
> **Autor:** [nome]
> **Contexto do projeto:** [link para proposta arquitetural ou nome do sistema]

## Contexto

[Por que essa decisão precisa ser tomada agora? Qual problema concreto ela resolve?
Qual atributo de qualidade ou restrição forçou? Inclua sintomas observáveis se houver
(latência de X, falhas em Y, custo de Z). Evite linguagem vaga tipo "para garantir
escalabilidade" — seja específico.]

## Decisão

[Frase afirmativa, em modo declarativo. "Adotamos X com configuração Y para o caso Z."
Não use condicional ("poderíamos adotar"). Não diga "consideramos várias opções e
escolhemos" — isso vai na próxima seção.]

## Justificativa

[Por quê. Referência explícita aos objetivos de negócio, atributos de qualidade
prioritários, restrições. Não vale "porque é boa prática" sem amarrar a uma necessidade
concreta deste projeto. Quanto mais ligado ao contexto, mais útil o ADR fica para
futuros leitores.]

## Alternativas consideradas

[Lista das opções que ficaram pelo caminho, cada uma com a razão honesta da rejeição.
Isso é o que diferencia um ADR útil de um documento decorativo — permite a quem ler
no futuro entender por que a alternativa óbvia foi descartada.]

### Alternativa A: [nome]

- **Descrição breve**: [...]
- **Por que foi descartada**: [...]

### Alternativa B: [nome]

- **Descrição breve**: [...]
- **Por que foi descartada**: [...]

## Consequências

### Positivas

- [O que essa decisão facilita ou habilita]
- [...]

### Negativas / Dívidas plantadas

[O que essa decisão dificulta ou compromete. Toda decisão tem ônus — explicite-o.
Se a dívida tem trigger conhecido, anote.]

- **Dívida**: [descrição]
  - **Quando vira problema**: [gatilho — volume, regulação, time, etc.]
  - **Como pagar**: [estratégia futura em alto nível]

### Neutras

[Mudanças necessárias que não são nem ganho nem perda, mas precisam ser planejadas.]

- [Migração de dados X]
- [Treinamento do time em Y]

## Implementação

[Notas práticas para quem vai implementar. Não é código — é direção. Pode citar
componentes afetados, ordem sugerida de migração, feature flags necessárias.]

- Tarefas planejadas: ver `docs/plans/PLAN-XXX-*.md` (procurar campo `Decisões base: ADR-XXX`)
- Componentes afetados: [...]
- Migração necessária: [Sim/Não — se sim, descrever brevemente]

## Referências

- [Link para discussão de design, RFC, papers, posts técnicos consultados]
- [Link para PRDs afetados, se houver]
- [Link para ADRs relacionados, se houver]
````

## Convenções

- **Numeração ADR-XXX**: 3 dígitos com zero à esquerda. Numeração global ao projeto, não reinicia.
- **Nome de arquivo**: `ADR-XXX-titulo-em-kebab-case.md`. Limitar a 60 caracteres no kebab.
- **Status `Revogada`**: não excluir o arquivo. Manter histórico e linkar para o ADR substituto. O ID nunca é reusado.
- **Status `Substituída por`**: usar quando a decisão evoluiu, não foi simplesmente revertida. O ADR original fica como histórico do raciocínio anterior.
- **Datas em ISO 8601**: `2026-06-30`, nunca `30/06/2026`. Facilita ordenação e parsing.
