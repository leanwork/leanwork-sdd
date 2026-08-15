# Catálogo de Estados de Tela

A seção mais valiosa da SPEC-UI. Protótipo costuma cobrir o caminho feliz; **a maioria dos bugs de interface nasce nos estados que ninguém desenhou**.

Cada estado ganha ID com sufixo: `UI-02.erro`, `UI-02.vazio`, `UI-02.carregando`. Isso permite que a tarefa do plano diga `Telas: UI-02 (default, erro, esgotado)` e que o review verifique estado a estado.

---

## Os estados universais

Aplicam-se a praticamente qualquer tela que busca ou envia dados.

### `.default`

O estado esperado, com dados presentes e tudo funcionando. É o que o protótipo sempre tem.

### `.carregando`

Enquanto a requisição está em andamento.

**Por que importa:** sem estado de carregamento definido, o dev improvisa — e cada tela ganha um spinner diferente, ou nenhum. Em listas, skeleton costuma ser melhor que spinner porque preserva a estrutura e reduz a sensação de espera.

**Especificar:** skeleton ou spinner? A tela inteira ou só a região que carrega? Os controles ficam desabilitados?

### `.vazio`

Não há dados para mostrar. **Diferente de erro** — nada falhou, simplesmente não há conteúdo.

**Por que importa:** é o primeiro estado que todo usuário novo vê, e é o mais negligenciado. Estado vazio bem-feito educa e oferece a próxima ação; malfeito parece bug.

**Especificar:** mensagem, ilustração (se houver), e principalmente a **ação sugerida** ("Criar primeira oferta").

Distinguir dois casos que costumam ser tratados como um só:
- **Vazio inicial** — o usuário nunca criou nada. Deve educar.
- **Vazio por filtro** — há dados, mas o filtro não retornou nada. Deve oferecer limpar o filtro.

### `.erro`

A requisição falhou.

**Especificar:** mensagem ao usuário (sem jargão técnico), se há botão de retentativa, e se o erro é da tela inteira ou de uma região. Erro que só mostra "Algo deu errado" sem ação é estado incompleto.

### `.semPermissao`

O usuário está autenticado mas não pode ver ou fazer aquilo.

**Quando obrigatório:** sempre que o PRD tiver seção de permissionamento com mais de um perfil.

**Especificar:** a tela inteira é bloqueada ou só elementos ficam ocultos/desabilitados? Elemento oculto e elemento desabilitado comunicam coisas diferentes — desabilitado revela que a funcionalidade existe.

---

## Estados por tipo de tela

### Listagem

| Estado | Obrigatório | Nota |
|---|---|---|
| `.default` | Sim | — |
| `.carregando` | Sim | Skeleton preferível a spinner |
| `.vazio` | Sim | Distinguir vazio inicial de vazio por filtro |
| `.vazioFiltro` | Quando há filtro | Deve oferecer limpar filtro |
| `.erro` | Sim | Com retentativa |
| `.carregandoMais` | Quando há paginação infinita | Diferente de `.carregando` inicial |
| `.parcial` | Quando há paginação | Indicar que há mais além do carregado |

### Formulário

| Estado | Obrigatório | Nota |
|---|---|---|
| `.default` | Sim | Campos vazios ou pré-preenchidos |
| `.validacao` | Sim | Erros de campo. Um por campo, não um alerta genérico |
| `.enviando` | Sim | Botão desabilitado, feedback de progresso. **Previne envio duplo** |
| `.sucesso` | Sim | Confirmação. Redireciona ou permanece? |
| `.erroEnvio` | Sim | Falha no servidor, distinta de erro de validação. **Preserva os dados digitados** |
| `.conflito` | Quando há concorrência | Alguém alterou o mesmo registro. Comum e quase sempre esquecido |

**A regra mais violada:** `.erroEnvio` que perde os dados do formulário. Especificar explicitamente que os dados são preservados.

### Detalhe / Visualização

| Estado | Obrigatório | Nota |
|---|---|---|
| `.default` | Sim | — |
| `.carregando` | Sim | — |
| `.naoEncontrado` | Sim | ID inválido ou registro removido. Distinto de `.erro` |
| `.erro` | Sim | Falha ao carregar |
| `.semPermissao` | Quando há permissionamento | — |

### Fluxo multi-etapa (wizard, checkout)

| Estado | Obrigatório | Nota |
|---|---|---|
| `.etapaN` | Sim | Um por etapa |
| `.processando` | Sim | Entre etapas, quando há validação no servidor |
| `.erroEtapa` | Sim | Falha em etapa específica — volta ou permanece? |
| `.abandonado` | Quando aplicável | Usuário volta depois. Recupera progresso? |
| `.expirado` | Quando há tempo limite | Reserva expirada, sessão encerrada |

### Ação destrutiva

| Estado | Obrigatório | Nota |
|---|---|---|
| `.confirmacao` | Sim | Diálogo antes de executar |
| `.processando` | Sim | Botão desabilitado |
| `.sucesso` | Sim | Feedback. Há desfazer? |
| `.erro` | Sim | Falhou — o estado anterior foi preservado? |

---

## Estados derivados de regras de negócio

Além dos genéricos, cada `RN-XX` que restringe ação costuma gerar um estado próprio.

Exemplos do domínio de ofertas relâmpago:

| Regra | Estado gerado |
|---|---|
| RN-03: limite de 1 unidade por cliente | `UI-02.limiteExcedido` |
| RN-05: estoque decrementado atomicamente | `UI-02.esgotado` |
| RN-01: janela de validade | `UI-01.encerrada` (oferta expira com a página aberta) |

**Procedimento para derivar:** percorrer os cenários Gherkin do PRD. Cada `Cenário [CA-XX]` cujo `Então` descreve rejeição, bloqueio ou mensagem de erro corresponde a um estado de tela.

Esse mapeamento é o principal argumento para a fase de protótipo existir no pipeline: sem ele, os cenários de erro do PRD ficam sem representação visual e viram improviso na implementação.

---

## Estados que costumam faltar

Lista de verificação rápida. Em protótipo real, estes são os mais ausentes:

- [ ] **Vazio por filtro** — tratado como vazio inicial, confundindo o usuário
- [ ] **Erro de envio preservando dados** — formulário que perde tudo ao falhar
- [ ] **Conflito de edição concorrente** — dois usuários editando o mesmo registro
- [ ] **Sessão expirada durante o fluxo** — especialmente em fluxo longo
- [ ] **Sem permissão em elemento específico** — botão que deveria estar oculto ou desabilitado
- [ ] **Estado transitório de regra de negócio** — item que esgota enquanto a página está aberta
- [ ] **Texto longo demais** — nome com 200 caracteres quebrando o layout
- [ ] **Zero e negativo** — valores de borda em campos numéricos
- [ ] **Offline / conexão instável** — quando o PRD menciona uso em campo ou mobile

Não é obrigatório especificar todos em toda tela. Mas **percorrer a lista** e decidir conscientemente o que se aplica é o que separa especificação de interface de catálogo de telas bonitas.

---

## Como registrar na SPEC-UI

```markdown
**Estados:**

| Estado | ID | Quando ocorre | O que o usuário vê | Origem |
|---|---|---|---|---|
| Padrão | `UI-02.default` | Oferta ativa, cliente elegível | Formulário de confirmação com preço | Protótipo |
| Enviando | `UI-02.enviando` | Confirmação em processamento | Botão desabilitado com spinner inline | Protótipo |
| Limite excedido | `UI-02.limiteExcedido` | Cliente já comprou (RN-03) | Alerta + link para voltar à listagem | Derivado de CA-05 |
| Esgotado | `UI-02.esgotado` | Estoque zerou (RN-05) | Alerta + sugestão de ofertas similares | Derivado de CA-06 |
| Erro de envio | `UI-02.erroEnvio` | Falha no servidor | Alerta com retentativa. **Dados preservados** | Derivado do PRD |
```

A coluna **Origem** importa: estado marcado como "Derivado" não passou por validação de design nem aprovação do cliente. Quem lê precisa saber disso antes de implementar.
