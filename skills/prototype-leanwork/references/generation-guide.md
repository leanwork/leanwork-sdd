# Guia de Geração — Arquétipos, Entrevista e Delegação

Procedimento para o modo geração: produzir protótipo navegável quando não existe um.

**Princípio central:** esta skill decide **quais telas existem, quais estados elas têm e o que aparece nelas**. O craft visual — tipografia, escala, paleta, composição — é delegado a skills de frontend disponíveis no ambiente.

---

## Ordem de precedência das fontes

Antes de perguntar qualquer coisa, extrair o máximo das fontes existentes:

### 1. PRD — define quais telas e quais estados

| Seção do PRD | O que deriva |
|---|---|
| Personas (5) | Quantos perfis de interface existem; se há área administrativa separada |
| Fluxos (7) | Sequência de telas; pontos de decisão viram bifurcação de navegação |
| Regras de negócio (8) | Validações, campos obrigatórios, estados desabilitados, mensagens |
| Critérios de aceite (9) | **Estados de tela.** Cada cenário de erro é um estado que precisa existir |
| Permissionamento (10) | Telas ou elementos condicionais por perfil; estado "sem permissão" |
| Diagrama de estados (12) | Se existe, cada estado da entidade tende a ter representação visual |

Os cenários Gherkin são a fonte mais subutilizada. Um `CA-05` que diz "cliente tenta comprar segunda unidade → mensagem de limite" **já é a especificação de um estado de tela**. Percorrer todos os cenários rende o inventário de estados quase pronto.

### 2. Arquitetura — define restrições

- Stack do frontend e biblioteca de componentes (se declarada em ADR)
- SPA vs SSR — afeta padrões de carregamento e navegação
- Restrições de acessibilidade, i18n, tema escuro
- Atributo de qualidade priorizado: se "Performance" é prioritária, o protótipo evita padrões pesados

### 3. Repositório — o protótipo herda, não reinventa

Antes de gerar qualquer coisa, verificar se já existe:

- Design tokens (`tailwind.config`, `theme.ts`, `tokens.css`, tema MUI)
- Componentes prontos em `components/` ou `ui/`
- Telas já implementadas de features anteriores

Se existe, **seguir**. Protótipo que não combina com as telas já existentes gera retrabalho e conversa desnecessária.

### 4. Entrevista — apenas as lacunas

Com PRD e arquitetura bem-feitos, normalmente sobram 2-3 perguntas.

---

## Arquétipos de interface

O arquétipo condiciona densidade, navegação, padrões de listagem e tom. Identificar cedo evita gerar um dashboard corporativo quando o PRD pedia um app de consumo.

### Admin / Dashboard

Operadores internos, uso diário e prolongado, alto volume de dados.

- Navegação lateral persistente
- Densidade alta — tabelas com muitas colunas, pouca respiração
- Ações em lote, filtros salvos, ordenação
- Estados de carregamento importam muito (listas grandes)
- Tom neutro e funcional; economia de palavras

### Ferramenta interna / App de operação

Tarefa específica e repetitiva, usuário treinado, velocidade acima de descoberta.

- Fluxo linear ou wizard
- Atalhos de teclado quando faz sentido
- Menos onboarding, mais eficiência
- Confirmações apenas para ações destrutivas

### E-commerce / Consumer

Usuário anônimo ou casual, primeira visita comum, conversão é o objetivo.

- Densidade baixa, hierarquia visual forte
- Imagem em destaque
- Fluxo de checkout com progresso visível
- Estados de erro precisam ser gentis e acionáveis
- Tom acessível

### Portal / Autoatendimento

Cliente externo acessando seus próprios dados, uso esporádico.

- Navegação óbvia, sem pressupor familiaridade
- Estado vazio precisa educar, não só informar
- Rotulagem sem jargão interno

### Site institucional

Conteúdo majoritariamente estático, objetivo de comunicação.

- Hierarquia tipográfica é o elemento estruturante
- Poucos estados dinâmicos
- Formulários pontuais (contato, cadastro)

---

## Entrevista — os seis blocos

Pular todo bloco já respondido pelas fontes anteriores. Perguntar no máximo 3 blocos de uma vez.

### Arquétipo
> Esse sistema se parece mais com: painel administrativo, ferramenta de operação, produto para cliente final, portal de autoatendimento, ou site institucional?

**Pula quando:** o PRD deixa óbvio pelas personas e fluxos.

### Dispositivo
> Desktop-first, mobile-first, mobile-only, ou responsivo pleno?

**Pula quando:** a arquitetura declara. Cuidado: "responsivo" costuma ser resposta automática — vale confirmar qual dispositivo é o **primário** de uso real.

### Fidelidade
> Wireframe (estrutura, campos e estados, sem tratamento visual) ou alta fidelidade (visual próximo do final)?

**Sempre perguntar.** Define o esforço e o tipo de delegação. Wireframe serve para validar fluxo rápido; alta fidelidade serve como referência de implementação.

### Identidade visual

Três cenários com condução diferente:

- **Cliente tem marca** → pedir referência concreta (site, manual, assets) e extrair. Não perguntar sobre cores.
- **Repositório tem design system** → detectar e seguir. Não perguntar nada.
- **Greenfield sem identidade** → **nunca fazer pergunta aberta**. Pergunta aberta sobre cor gera resposta ruim e protótipo genérico. Propor 2-3 direções concretas e nomeadas:

> Sem identidade definida, proponho três direções:
>
> **A.** Neutra e densa — cinzas frios, tipografia compacta, bordas sutis. Boa para ferramenta de uso intenso.
> **B.** Quente e espaçosa — respiração generosa, tipografia maior, acento de cor pontual. Boa para produto voltado ao cliente final.
> **C.** Corporativa sóbria — azul institucional, alto contraste, visual conservador. Boa quando o cliente é enterprise tradicional.

### Densidade e tom
> Interface densa tipo ERP (muita informação por tela) ou espaçosa tipo produto de consumo? Tom formal ou descontraído nos textos?

**Pula quando:** o arquétipo já implica fortemente.

### Restrições
> Alguma restrição de acessibilidade, tema escuro obrigatório, múltiplos idiomas, ou biblioteca de componentes que precisa ser usada?

**Pula quando:** a arquitetura já lista tudo isso.

---

## Delegação do craft visual

Esta skill **não** decide tipografia, escala tipográfica, paleta, espaçamento ou composição. Ela monta o briefing estruturado e delega.

### Briefing a passar para a skill de frontend

```
Arquétipo: [admin | operação | consumer | portal | institucional]
Dispositivo: [desktop-first | mobile-first | mobile-only | responsivo]
Fidelidade: [wireframe | alta fidelidade]
Stack: [extraída da arquitetura]
Biblioteca obrigatória: [se houver]
Tokens existentes: [se o repositório tiver]
Direção visual: [A/B/C escolhida, ou marca do cliente]
Densidade: [alta | média | baixa]
Tom: [formal | neutro | descontraído]
Restrições: [acessibilidade, tema escuro, i18n]

Telas a gerar:
- UI-01 [nome] — [propósito] — estados: default, vazio, carregando, erro
- UI-02 [nome] — [propósito] — estados: default, limite, esgotado
[...]

Componentes reutilizáveis identificados:
- [componente] — usado em UI-01, UI-04 — estados: [...]
```

### Quando há skill de frontend disponível

Passar o briefing e deixar que ela conduza as decisões visuais. Não sobrescrever escolhas de design que ela fizer — o papel desta skill acabou na estrutura.

### Quando não há skill de frontend

Gerar HTML funcional focado em **estrutura e estados**, e declarar no documento:

> **Fidelidade:** Wireframe. Nenhuma skill de design de interface estava disponível no ambiente — o protótipo cobre estrutura, campos e estados, sem tratamento visual final.

Isso é honesto e útil: um wireframe correto vale mais que uma tentativa de alta fidelidade malfeita.

---

## O que gerar

### Sempre

- Uma tela por `UI-XX` do inventário
- **Todos os estados listados**, não só o caminho feliz. Estado de erro e vazio são justamente o que protótipo costuma ignorar e o que mais gera bug depois
- Navegação funcional entre telas, quando o formato permitir
- Dados de exemplo plausíveis e coerentes com o domínio

### Nunca

- Telas que o PRD não pediu. Se parece que falta uma tela, **apontar como lacuna** em vez de gerar por conta própria
- Regras de negócio novas. O protótipo materializa `RN-XX` existentes; não cria
- Dados que induzam a erro (valores irreais, textos "lorem ipsum" em campos onde o conteúdo importa)

---

## Checklist antes de fechar a geração

- [ ] Todo `CA-XX` do PRD acontece em alguma tela ou está declarado como cenário de backend
- [ ] Todo `RN-XX` de interface se manifesta em alguma tela
- [ ] Cada tela tem os estados obrigatórios do seu tipo (ver `screen-states.md`)
- [ ] Componentes repetidos foram identificados como reutilizáveis
- [ ] Tokens usados estão documentados na seção 2 da SPEC-UI
- [ ] Nenhuma tela foi gerada sem respaldo no PRD
- [ ] Fidelidade declarada honestamente no cabeçalho do documento
