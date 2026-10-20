# Sensor de discriminação

Protocolo do eixo 4 para responder a pergunta que "o teste existe e passa" não responde: **este teste pegaria o bug?**

A técnica é injeção de falha. Introduz-se um defeito deliberado no comportamento sob teste e observa-se se a suíte quebra. Se quebrar, o teste **discrimina** aquele comportamento — o mutante morreu. Se passar com o defeito no lugar, o teste não discrimina, e o critério que ele supostamente cobre segue descoberto.

O protocolo é stack-agnóstico. Nenhuma ferramenta de mutation testing é obrigatória — quando a stack do projeto tem uma boa (Stryker, PIT, mutmut, `cargo-mutants`), usá-la é preferível nas tarefas de risco alto, mas a ausência dela nunca é motivo para pular o sensor.

---

## Antes de tudo: onde o sensor roda

**O sensor nunca muta a worktree do usuário.** Ele injeta um defeito em código real; se o isolamento falhar, o defeito fica no repositório de quem pediu a review. Todo o protocolo abaixo existe em torno dessa garantia, e os passos 1 e 6 são o que a sustenta.

### `git stash` é proibido

Não como preferência de estilo — porque **não funciona** para este uso:

- Numa árvore limpa, `git stash` **não cria entrada nenhuma**. O comando sai sem erro e sem ter guardado nada.
- O `git stash pop` seguinte, portanto, não tem o que restaurar — e, pior, não reverte uma mutação que foi aplicada **depois** do stash.
- Resultado: o defeito injetado permanece na worktree real, e o revisor acredita que restaurou.

A sequência "stash → mutar → testar → pop" parece simétrica e não é. Usar `git worktree`, ou a cópia de arquivos descrita no passo 2.

---

## Os sete passos

A ordem importa. O baseline vem antes de qualquer escrita, e a verificação de isolamento vem depois de qualquer descarte.

### 1. Capturar o baseline

```bash
git status --porcelain
```

Na worktree **real**, antes de tocar em qualquer coisa. Guardar a saída literal. É contra ela que o passo 6 compara.

Não exigir árvore limpa: revisar trabalho não commitado é caso normal. O que importa é que o estado no fim seja **idêntico** ao do começo, seja ele qual for.

### 2. Preparar o scratch isolado

```bash
git worktree add <scratch> HEAD
```

`<scratch>` fora da árvore do projeto (um temporário do sistema). O scratch nasce em `HEAD`; se a review é de trabalho não commitado, copiar para dentro dele os arquivos modificados antes de mutar.

**Sem git, ou com `git worktree` indisponível:** copiar **apenas os arquivos afetados pela tarefa** para um diretório temporário e apontar o runner de testes para lá. Copiar o repositório inteiro não é alternativa aceitável — é lento, e a cópia larga aumenta a chance de o runner escrever de volta em caminho errado.

**Repositório em merge ou rebase em andamento:** `git worktree add` falha ou produz estado confuso. Não tentar contornar. Reportar ao usuário que o sensor não rodou e por quê, e seguir a review sem ele — com a lacuna declarada no relatório. Um sensor que exige do usuário abortar um rebase em andamento para acontecer custa mais do que entrega.

### 3. Injetar a falha comportamental

**Somente dentro do scratch.** A mutação vai no código **novo da tarefa**, não em código pré-existente — o sensor mede os testes que esta review está avaliando.

Catálogo de mutações, todas comportamentais:

| Mutação | Exemplo |
|---|---|
| Inverter condição booleana | `if (x)` → `if (!x)`; `>` → `>=` |
| Trocar valor de retorno | status code errado, campo errado, `0` no lugar do valor calculado |
| Off-by-one | limite de laço ou índice deslocado em 1 |
| Remover efeito colateral | tirar a escrita que a `RN-XX` exige |

Mutação de formatação, de nome de variável ou de comentário não serve: não muda comportamento, então não mede nada.

Escolher a mutação pela **implementação errada mais provável** daquele trecho, não pela mais fácil de aplicar.

### 4. Rodar os testes

Rodar, contra o scratch, os testes que cobrem o código mutado. A suíte inteira serve, mas é desperdício quando o alvo é conhecido.

### 5. Confirmar que o mutante morreu, e descartar o scratch

Mutante **morto** = os testes falharam. É o resultado esperado.

Descartar o scratch antes de qualquer conclusão:

```bash
git worktree remove <scratch> --force
```

### 6. Verificar o isolamento

```bash
git status --porcelain
```

De novo, na worktree real, e comparar com o baseline do passo 1.

**Divergiu: PARE.** Restaurar a worktree ao estado do baseline, avisar o usuário, e tratar a execução do sensor como **inválida**. Resultado de run inválida **não se reporta** — nem como mutante morto, nem como sobrevivente. Uma run cujo isolamento falhou não diz nada sobre a qualidade dos testes; diz que o procedimento quebrou.

Este é o passo que torna a técnica segura, e é o primeiro a ser cortado numa reescrita apressada. Sem ele o sensor é uma forma de deixar defeito no código dos outros.

### 7. Interpretar o resultado

**Mutante sobrevivente** — os testes passaram com o defeito no lugar — significa que os testes não discriminam aquele comportamento: **finding `Bloqueante`**. Teste que não pega o bug é teste que não existe.

O finding aponta a **asserção fraca**, não a mutação. A correção certa é fortalecer a asserção para verificar o comportamento real; a correção errada é acrescentar um teste que mate exatamente aquela mutação e mais nada.

---

## Profundidade proporcional ao risco

| Contexto | Profundidade |
|---|---|
| Padrão — toda tarefa que tenha teste | 1-3 mutações no código novo de maior risco |
| Tarefa que toca dinheiro, autenticação/autorização ou integridade de dados | 5+ mutações cobrindo todos os ramos, ou a ferramenta de mutation testing da stack quando existir |

A classificação de risco sai de duas fontes objetivas: as `RN-XX` que a tarefa declara em `Implementa:`, e os atributos de qualidade priorizados na proposta arquitetural. **Não sai do palpite do revisor** — senão a profundidade acompanha o tempo disponível em vez do risco.

---

## Registro no relatório

Toda execução do sensor vai para a seção "Sensor de discriminação" do relatório, com a profundidade, o mecanismo de isolamento usado e uma linha por mutação tentada. Sensor que roda e não é registrado é invisível e não auditável — exatamente o tipo de regra que o pipeline existe para eliminar.

Quando o sensor **não** rodou (sem suíte executável, repositório em rebase, ambiente sem execução de código), a seção registra isso e a razão. Ausência declarada é informação; seção omitida é silêncio que passa por aprovação.
