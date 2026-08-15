# Guia de Ingestão — Extração por Formato

Procedimento para extrair a especificação de interface a partir de um protótipo existente.

**Ordem de tentativa recomendada:** HTML exportado → imagens → Figma via MCP → Lovable/v0 exportado para repositório.

**Regra que vale para todos os formatos:** ao final da extração, declarar explicitamente **o que não foi possível extrair** antes de perguntar. O usuário precisa saber onde a skill está cega. Extração silenciosamente incompleta produz SPEC-UI que parece completa e não é.

---

## HTML / React no repositório — melhor caso

Fonte mais rica. O agente lê os arquivos direto.

### O que extrair

| Informação | Onde procurar |
|---|---|
| Inventário de telas | Arquivos de rota (`App.jsx`, `routes.tsx`, `pages/`, `app/` no Next), ou arquivos HTML separados |
| Rotas | Definição de router, ou nome dos arquivos |
| Campos e controles | `<input>`, `<select>`, `<button>`, componentes de formulário |
| Componentes reutilizáveis | Imports repetidos entre telas; pasta `components/` |
| Estados implementados | Renderização condicional (`{loading && ...}`, `{error && ...}`, ternários), variantes de prop |
| Tokens de design | `tailwind.config.js`, `theme.ts`, variáveis CSS, `tokens.css` |
| Navegação | `<Link>`, `navigate()`, `href` |

### Procedimento

1. Mapear a estrutura de pastas para identificar onde vivem telas e componentes
2. Ler os arquivos de rota primeiro — dão o inventário completo de uma vez
3. Para cada tela, ler o arquivo e extrair campos, estados e navegação
4. Identificar componentes importados por mais de uma tela → seção de reutilizáveis
5. Ler configuração de tema para os tokens

### Limitações a declarar

- **Estados não implementados no protótipo.** Se o protótipo é estático e não tem tratamento de erro, esse estado não existe no código — mas provavelmente é necessário. Derivar do PRD e marcar origem como "Derivado do PRD".
- **Intenção de negócio.** O código mostra que um campo é obrigatório; não mostra *por quê*. O mapeamento com `RN-XX` exige leitura do PRD, não do código.
- **Dados mockados.** Protótipo costuma ter dados fixos. Não confundir mock com regra de negócio.

---

## Imagens (PNG, JPG, screenshots) — segundo caminho

Funciona melhor do que se espera. O agente lê imagens e identifica layout, hierarquia, campos, botões, estados visíveis e cores aproximadas.

### O que extrair

| Informação | Confiabilidade |
|---|---|
| Layout e hierarquia visual | Alta |
| Campos, rótulos e controles | Alta |
| Texto visível (rótulos, mensagens, botões) | Alta |
| Estrutura de navegação interna (menu, abas, breadcrumb) | Média |
| Cores | Aproximada — identifica "azul escuro", não o hex exato |
| Tipografia | Aproximada — identifica serifada/sem serifa, peso, não a família exata |
| Espaçamento e escala | Baixa — não medir em pixel a partir de imagem |

### Procedimento

1. Processar uma imagem por vez, atribuindo `UI-XX` na ordem em que foram fornecidas
2. Para cada imagem: propósito da tela, campos, controles, textos, estado aparente
3. Após todas, apresentar o inventário e **pedir confirmação dos nomes e da ordem**
4. Perguntar sobre navegação — imagens não carregam essa informação

### Limitações a declarar sempre

- **Navegação entre telas.** A imagem não diz qual tela leva a qual. Sempre perguntar.
- **Estados não capturados.** Se o usuário mandou só o estado padrão, os estados de erro, vazio e carregando não existem no material. Derivar do PRD e marcar origem.
- **Valores exatos de token.** Cor e fonte são aproximações. Marcar como tal na seção 2 da SPEC-UI.
- **Comportamento dinâmico.** Hover, transição, validação em tempo real, scroll infinito — nada disso aparece em imagem estática.
- **Conteúdo cortado.** Screenshot de tela longa pode estar truncado. Perguntar se há mais conteúdo abaixo da dobra.

### Boa prática a sugerir ao usuário

Quando o material for só imagem, vale sugerir (sem insistir) que ele mande também os prints dos estados de erro e vazio, se existirem no protótipo. É o material que mais falta e o que mais gera retrabalho depois.

---

## Figma via MCP — quando o cliente fornece acesso

Requer o MCP do Figma conectado no ambiente. Sem MCP, link do Figma **não funciona** — o conteúdo é canvas renderizado atrás de autenticação, não HTML legível.

### O que extrair

| Informação | Onde |
|---|---|
| Inventário de telas | Frames de nível superior |
| Estados | Frames variantes, ou nomeação (`Checkout / erro`, `Checkout / vazio`) |
| Componentes | Biblioteca de componentes e instâncias |
| Tokens | Estilos de cor, texto e efeito publicados |
| Hierarquia | Árvore de camadas |
| Fluxo | Protótipo interativo, quando configurado |

### Procedimento

1. Listar os frames de nível superior → inventário de telas
2. Identificar variantes de componente → estados
3. Extrair estilos publicados → tokens (valores exatos, diferente do caso imagem)
4. Se houver protótipo interativo configurado, extrair as conexões → navegação
5. Perguntar sobre o que a estrutura do arquivo não deixa claro

### Limitações a declarar

- **Arquivo desorganizado.** Figma sem nomeação consistente de frames dificulta identificar o que é tela, o que é rascunho e o que é variante. Perguntar em vez de adivinhar.
- **Comportamento dinâmico.** Mesmo com protótipo interativo, regras de validação e comportamento condicional não estão no Figma.
- **Frames abandonados.** Arquivos reais têm telas antigas e exploratórias. Confirmar quais entram no escopo.

### Sem MCP disponível

Informar o usuário e oferecer as alternativas:

> Não tenho o MCP do Figma conectado, então não consigo ler o arquivo direto. Duas opções: exportar as telas como PNG e anexar aqui, ou colar o código do Dev Mode das telas principais. A primeira é mais rápida; a segunda dá tokens exatos.

---

## Lovable / v0 / Bolt — quando o cliente usou ferramenta de geração

### Caminho recomendado: código exportado para o GitHub

Lovable e v0 exportam para repositório. Uma vez exportado e clonado, **a ingestão é idêntica ao caso HTML/React** — o melhor caso.

Sempre preferir esse caminho. Sugerir ao usuário:

> Se o protótipo do Lovable estiver exportado para o GitHub, me passa o caminho da pasta clonada — a extração fica muito melhor do que pelo link do preview, e você fica com o código versionado para servir de base na implementação.

### Caminho alternativo: link do preview publicado

Funciona parcialmente. É uma SPA React: o HTML servido é um shell que hidrata via JavaScript, então fetch simples traz pouco conteúdo útil.

Com ferramenta de navegação disponível no ambiente, o agente consegue navegar e ler o DOM renderizado — aí a extração funciona bem, incluindo navegação entre telas.

Sem ferramenta de navegação, declarar a limitação e sugerir exportação ou screenshots.

### Cuidado específico com protótipos gerados por IA

- **Dados mockados são abundantes.** Ferramentas de geração enchem a tela de dados fictícios. Não confundir com requisito.
- **Telas que ninguém pediu.** A ferramenta pode ter gerado telas por conta própria. Cruzar com o PRD antes de aceitar tudo como escopo.
- **Estados frequentemente ausentes.** Protótipo gerado costuma cobrir só o caminho feliz.

---

## Modo híbrido — protótipo parcial

Comum na prática: o cliente entregou as telas principais, mas estados de erro e telas administrativas não foram desenhados.

### Procedimento

1. Ingerir tudo que existe, seguindo o guia do formato correspondente
2. Cruzar com o PRD (Fase 4 da skill) para identificar o que falta
3. **Apresentar as lacunas ao usuário antes de gerar qualquer coisa**
4. Para cada lacuna, deixar a decisão com ele: gerar a tela, ajustar o PRD, ou aceitar como fora de escopo
5. O que for gerado entra no documento marcado com origem "Gerado", nunca misturado com "Protótipo" sem distinção

A distinção de origem importa: uma tela gerada não passou por validação de design nem por aprovação do cliente. Quem lê a SPEC-UI precisa saber disso.

---

## Checklist antes de fechar a ingestão

- [ ] Todas as telas do material receberam `UI-XX`
- [ ] Nomes e ordem das telas foram confirmados pelo usuário
- [ ] Navegação entre telas está mapeada (perguntada, quando não extraível)
- [ ] Estados de cada tela estão listados, com origem marcada
- [ ] Componentes que aparecem em mais de uma tela foram identificados
- [ ] Tokens extraídos, com marcação de aproximado quando aplicável
- [ ] Lacunas declaradas explicitamente, sem preenchimento por suposição
- [ ] Cruzamento com PRD feito nas duas direções
