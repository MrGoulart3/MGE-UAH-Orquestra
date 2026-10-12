# Montar a arquitetura “orquestra de IAs” (herdr + Claude Code + IAs auxiliares)

> **Para o Claude que está lendo:** este arquivo é um roteiro para montar, na máquina do seu usuário, a mesma
> arquitetura que o Mario usa no PC dele. Siga as fases em ordem. **No início de cada fase, rode a checagem
> “Já feito?”: se passar, pule a fase e siga para a próxima.** O usuário programa apps (não roda cálculo
> científico), então adapte os exemplos a repositórios de código.
> Converse em português com o usuário. Antes de instalar qualquer coisa ou mexer em configuração global
> (`~/.claude`, crontab, firewall), mostre o que vai fazer e peça confirmação. Nunca grave senhas ou chaves de
> API em arquivos versionados nem em mensagens; peça ao usuário para colar as chaves num arquivo local
> (ex.: `~/.config/<servico>_key`, permissão 600).

## Resultado final (o que o usuário terá)
- **herdr** com um *workspace* por projeto (app), cada um com abas `claude`, `codex`, `opencode`, `groq`, `openrouter`.
- Um **space central** (“diretrizes”) que recebe ordens do usuário, classifica (PERMANENTE/PONTUAL), registra
  e repassa a todos os spaces.
- **Economia de créditos**: tarefas simples vão a modelos gratuitos (opencode/groq/OpenRouter), implementação
  média/longa ao Codex, decisões e revisão final ao Claude.
- **Trabalho contínuo**: cada space mantém `CONTINUIDADE.md`; um vigia sem IA retoma os spaces quando o limite
  de créditos volta.
- **OMC** (oh-my-claudecode) com agentes executor/verifier/explore e, opcionalmente, um **roteador de modelos**.
- **Graphify** (grafo de conhecimento por projeto) e **vault do Obsidian** gerado a partir do grafo.
- Opcional (só se o usuário quiser): segunda máquina via **Tailscale**, celular entrando no terminal, avisos push.

---

## Fase 0 — Diagnóstico (sempre rode)
1. Identifique: sistema operacional, shell, RAM, núcleos (`uname -a; nproc; free -g` ou equivalente no Windows/macOS).
2. Verifique o que já existe: `claude --version`, `herdr --version`, `codex --version`, `opencode --version`,
   `claude plugin list` (procure `oh-my-claudecode`), `ls ~/.claude/skills`, `crontab -l`.
3. Pergunte ao usuário: quais projetos (pastas) quer transformar em spaces; se tem plano do ChatGPT (para o Codex);
   se aceita criar contas grátis no Groq e no OpenRouter.
4. Monte uma lista de fases **já feitas** e diga ao usuário quais vai pular.

## Fase 1 — Ferramentas básicas
**Já feito?** `claude`, `herdr`, `codex`, `opencode` respondem a `--version`.
- **Claude Code**: instale pelo método oficial da Anthropic (veja a documentação atual).
- **herdr**: multiplexador de terminal para agentes (workspaces, abas, `herdr agent list/prompt/read`).
  Instale pelo README oficial do herdr. **Se o herdr não estiver disponível para este sistema**, use `tmux`
  como substituto (uma sessão por projeto, janelas `claude`/`codex`/`opencode`) e, no lugar de
  `herdr agent prompt`, use `tmux send-keys -t <sessão>:<janela> "<texto>" Enter`; o resto do roteiro vale igual.
- **Codex CLI** (OpenAI): `npm i -g @openai/codex` e login com a conta ChatGPT do usuário. Usa o modelo padrão do plano.
- **opencode**: instale pelo site oficial. Modelo grátis principal: `opencode/nemotron-3-ultra-free`.
- Integração do herdr com os agentes: `herdr integration status` (deixe claude/codex/opencode em `current`).

## Fase 2 — IAs gratuitas de apoio
**Já feito?** `groq "diga oi"` responde e `opencode run -m opencode/nemotron-3-ultra-free "diga oi"` responde.
1. **Groq** (muito rápido, grátis): o usuário cria a chave em console.groq.com e salva em `~/.config/groq_key`.
   Crie o script `~/bin/groq` (Python, só biblioteca padrão) que chama
   `https://api.groq.com/openai/v1/chat/completions` com modelo padrão `openai/gpt-oss-120b`
   (opção `-m` para `qwen/qwen3-…`, `llama-3.1-8b-instant`), lê a pergunta dos argumentos e, se houver, um arquivo
   pelo stdin (corte em ~12 mil caracteres), `max_tokens` ~900, imprime só a resposta.
2. **OpenRouter** (reserva grátis, limite diário baixo): chave em openrouter.ai; configure no opencode. Modelos
   `:free` úteis: `openrouter/poolside/laguna-s-2.1:free`, `openrouter/cohere/north-mini-code:free` (código),
   `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free` (raciocínio).
3. Regra que vai para todos os spaces: **nunca enviar segredos, dados de clientes ou código proprietário
   sensível aos modelos gratuitos.**

## Fase 3 — OMC (oh-my-claudecode)
**Já feito?** `claude plugin list` mostra `oh-my-claudecode` habilitado em escopo user.
- Instale o plugin pelo marketplace oficial do OMC e rode o setup dele (`/oh-my-claudecode:omc-setup`).
- Confirme que existem os agentes `oh-my-claudecode:executor`, `:verifier`, `:explore`, `:code-reviewer`.
- Regra de delegação para os spaces: executor em **Sonnet** produz; verifier confere; explore busca; **Opus** só para
  planejamento, análise difícil e verificação final; nunca Haiku para conteúdo técnico.

## Fase 4 — Scripts de apoio sem IA
**Já feito?** `capacidade_pc` imprime um veredito.
1. `~/bin/capacidade_pc`: lê RAM disponível, carga (load) e quantas sessões de codex/opencode estão abertas;
   imprime **OK** (pode abrir sessões), **APERTADO** (só comandos pontuais `opencode run`/`groq`) ou **LOTADO**
   (não abrir nada; avisar o usuário). Ajuste os limites à máquina (ex.: OK se RAM livre ≥ 4 GB e load ≤ 60% dos núcleos).
2. (Opcional, ver Fase 12) `~/bin/avisar "Título" "mensagem" [alta]` para push no celular.

## Fase 5 — O space central (diretrizes)
**Já feito?** existe uma pasta `diretrizes/` com `CLAUDE.md`, `diretrizes.md` e `BLOCOS_PERMANENTES.md`.
1. Crie `~/<base>/diretrizes/` e um workspace herdr `diretrizes` com as abas padrão.
2. `CLAUDE.md` do central deve dizer:
   - papel: coordenar os outros spaces; responder em português;
   - **PERMANENTE** → registrar em `diretrizes.md` (data + texto), acrescentar a linha `>` em `BLOCOS_PERMANENTES.md`
     e pedir a cada space que grave no próprio `CLAUDE.md`; **PONTUAL** → repassar e anotar como pontual;
     se o usuário não disser qual é, perguntar;
   - como repassar: `herdr agent list`, depois
     `herdr agent prompt <agente> "DIRETRIZ PERMANENTE (via diretrizes): <texto>. Registre no seu CLAUDE.md e confirme." --wait --timeout 300000`;
     não interromper agente em `working` (tentar depois);
   - uma tabela-mapa dos spaces (nome, pasta, observações) mantida atualizada.
3. `BLOCOS_PERMANENTES.md` = fonte única das regras que todo space novo recebe no topo do `CLAUDE.md`. Comece com:
   - **Economia de créditos**: simples → `opencode run -m opencode/nemotron-3-ultra-free "<tarefa>"` ou `groq`;
     Codex = implementação média/longa; Claude = plano, decisão e conferência final; não confiar em decisão vinda só do gratuito.
   - **IAs secundárias automáticas**: em stand-by, manter Codex/opencode fechados (RAM); ao gastar créditos,
     rodar `capacidade_pc` e, se OK, usar Codex/opencode/groq automaticamente, fechando as sessões ao terminar.
   - **RAM**: sessões interativas só quando usar; preferir comandos pontuais.
   - **Créditos acabaram**: antes de parar, gravar o estado no `CONTINUIDADE.md`; quando voltar, continuar sem esperar.
   - **Ditado por voz** (se o usuário usa): deduzir palavras trocadas; perguntar se impossível entender.
   - **Segurança**: nada de segredos/dados sensíveis aos gratuitos nem em avisos.

## Fase 6 — Molde de space novo (skill `preparar-space`)
**Já feito?** existe `~/.claude/skills/preparar-space/SKILL.md`.
Crie a skill (gatilhos: “novo space”, “novo projeto”, “preparar projeto”) com estes passos verificáveis:
1. Workspace herdr na raiz do projeto com abas `claude`, `codex`, `opencode`, `groq`, `openrouter`
   (selecionar abas pelo NOME com `herdr tab list`); iniciar o Claude (`herdr agent start <nome> --kind claude --pane <id>`).
   No primeiro start o Claude pede confiança na pasta: confirme com o usuário.
2. `CLAUDE.md` curto: todos os blocos `>` de `BLOCOS_PERMANENTES.md` no topo; objetivo; estado; regras do projeto;
   seção “Delegação e modelos”; seção “Coordenação” apontando para o space central.
3. `CONTINUIDADE.md` com: Estado, Pendências, Tarefas em andamento, Próximo passo, **PERGUNTAS PARA O USUÁRIO**.
4. `.graphifyignore` (antes do primeiro `/graphify`): `node_modules/`, `dist/`, `build/`, `.next/`, `coverage/`,
   `*.lock`, binários, mídia, `.env*`, segredos.
5. Avisar o central (nome, pasta, workspace) para entrar no mapa.
6. Verificação final por um subagente barato (explore/Sonnet) em modo só leitura, PASS/FAIL por item.
Depois, rode a skill para cada projeto que o usuário listou na Fase 0.

## Fase 7 — Trabalho contínuo
**Já feito?** existe o vigia de retomada no crontab (`@reboot ... retomar_apos_limite.sh`).
1. Script `~/bin/retomar_apos_limite.sh todos nunca` (bash, sem IA): a cada 10 min percorre `herdr agent list`;
   para cada Claude parado (`idle`/`done`) cuja tela (`herdr agent read`) mostre aviso de limite
   (“hit your limit”, “usage limit”, “resets …”), envia:
   “RETOMADA AUTOMATICA: leia o seu CONTINUIDADE.md e continue de onde parou, com economia; se não houver nada, fique em stand-by.”
   Registra em log. Coloque `@reboot sleep 180; ~/bin/retomar_apos_limite.sh todos nunca` no crontab.
2. Combine com o usuário as rotinas:
   - **Antes de sair/dormir**: o central pede a todos “trabalhe com autonomia e economia; não mande perguntas,
     anote-as no CONTINUIDADE”.
   - **Contexto > ~50%**: o central pede ao space “grave o estado no CONTINUIDADE e avise quando estiver pronto”,
     envia `/compact` com o que preservar e depois “prossiga”.
   - **Manhã**: o central junta as “PERGUNTAS PARA O USUÁRIO” e o que ficou pronto num resumo curto.
3. Monitoramento de tarefas longas (builds, deploys, testes demorados): scripts simples ou `Monitor`, nunca
   checagens agendadas do Claude de poucos em poucos minutos.

## Fase 8 — Roteador de modelos (avançado, opcional)
**Já feito?** existe `~/.claude/hooks/model-router/` registrado em `~/.claude/settings.json`.
Pergunte ao usuário se quer. Se sim, crie dois hooks Node:
- `UserPromptSubmit`: dá nota ao pedido (palavras como arquitetura/segurança/bug difícil, tamanho, stack trace)
  → **LOW** (resolver direto/Sonnet), **MEDIUM** (Sonnet implementa, Codex revisa o diff), **HIGH** (Opus analisa
  + Codex em modo leitura dá 2ª opinião em paralelo; divergências resolvidas com evidência; verificação por Opus).
  Injeta o plano como contexto. Atalhos no pedido: `#high`, `#medium`, `#low`, `#noroute`.
- `PreToolUse` em `Agent|Task`: ajusta o `model` do subagente (nunca Haiku para conteúdo técnico; agentes leves
  como explore podem ficar em Sonnet).
- `config.json` com limiares e `enabled`; log em `routing.jsonl` para calibrar.

## Fase 9 — Graphify e Obsidian
**Já feito?** cada space tem `graphify-out/graph.json`; existe `workflow_digestion/obsidian-vault` em algum space.
1. Instale a skill/CLI `graphify` (pacote `graphifyy` no pip) e rode `/graphify` em cada projeto **depois** do
   `.graphifyignore`. Atualizações sempre incrementais (`--update`).
2. Para o vault do Obsidian, use o pipeline **Workflow_Digestion** (MarkItDown → Graphify → Obsidian):
   `git clone https://github.com/fatioleg/Workflow_Digestion` numa pasta própria (não altere o original, sem push).
3. **Regra de custo (lição aprendida):** gere o vault **a partir do grafo existente**:
   `python scripts/run_pipeline.py <pasta> --skip-graphify` (etapa sem LLM). Reler o texto completo de muitos
   documentos com vários subagentes zera o limite de créditos em poucas horas: se precisar, faça em lotes de 3–4
   arquivos, 1 subagente Sonnet por vez, conferindo o medidor de 5 h e parando acima de ~50%.
4. Melhorias periódicas (à noite, um space por vez): fundir entidades duplicadas, corrigir rótulos, ligar
   resultados novos a conceitos; registrar em `graphify-out/MELHORIAS_NOITE.md`.

## Fase 10 — Fluxo para apps e segurança
**Já feito?** os `CLAUDE.md` dos apps têm a seção “Fluxo de desenvolvimento”.
Acrescente a cada space de app:
- Um space por repositório. Tarefas paralelas no mesmo repo → `git worktree` (uma pasta/branch por tarefa).
- Fluxo: Claude planeja → Codex ou executor (Sonnet) implementa → testes → revisão independente
  (verifier/code-reviewer ou `codex exec -s read-only`) → Claude aprova. Quem escreve não aprova o próprio trabalho.
- Commits só quando o usuário pedir; branch antes de mexer na principal.
- Segredos só em `.env`/gerenciador (fora do git); nunca nos modelos gratuitos, nos avisos ou nos logs.

## Fase 11 — Extras úteis (pergunte se quer)
- **Painel do PC**: servidor HTTP leve (Python, biblioteca padrão, `nice 19`, histórico em memória) que mostra
  CPU, RAM, disco e consumo **por space** (soma os processos pelo `cwd` dentro da pasta do projeto). Só leitura,
  escutando em `127.0.0.1` (e na interface do Tailscale, se houver).
- **Central de páginas**: se o usuário publica páginas (Artifacts) no claude.ai, crie uma página-mãe com banco de
  dados e uma regra permanente para todo space cadastrar ali cada página nova.

## Fase 12 — OPCIONAL: segunda máquina, Tailscale e celular
**Pergunte ao usuário antes:** “Quer configurar acesso de outra máquina e do celular a este computador
(Tailscale, SSH, avisos no celular)? Posso pular esta parte.” **Só prossiga se ele disser que sim.**
1. **Tailscale** nos aparelhos (mesma conta ou compartilhamento entre contas). Anote o endereço da rede de cada um
   (não publique esses endereços).
2. **SSH só com chave** da outra máquina para esta (`ssh-keygen -t ed25519`, `authorized_keys`, desligar senha se o
   usuário concordar). Alias em `~/.ssh/config`.
3. Na outra máquina, o usuário entra por SSH e usa o mesmo herdr (`herdr` anexa aos workspaces). Se outra **pessoa**
   usar, marque os spaces dela no mapa do central e combine: ela não para nem apaga nada dos outros; pastas próprias
   de entrada/saída (ex.: `~/recebidos_<nome>`, `~/enviar_<nome>`).
4. **Celular**: Termux (Android) ou um app SSH (iOS) + Tailscale; RustDesk para ver a tela, se quiser.
5. **Avisos push**: app **ntfy** no celular com um tópico aleatório longo (guardado em `~/.config/ntfy_topic`);
   script `~/bin/avisar` faz `curl -H "Title: …" -d "…" https://ntfy.sh/<tópico>`. O servidor é público: nunca
   mande senhas, endereços ou dados sensíveis. Regra para os spaces: avisar só quando algo termina, falha ou
   precisa de aprovação, poucos avisos por dia.
6. **Firewall**: libere portas (ex.: painel) só na interface `tailscale0`.
7. **Troca de arquivos com o notebook**: pasta `_para_notebook/` em cada projeto que o notebook puxa
   periodicamente; um `PEDIDO_<assunto>.md` quando o Claude de lá precisa agir.

## Checklist final
- [ ] Fase 0 registrada (o que foi pulado e por quê).
- [ ] Ferramentas e IAs gratuitas respondendo.
- [ ] OMC ativo; regra de delegação nos `CLAUDE.md`.
- [ ] Space central com `diretrizes.md`, `BLOCOS_PERMANENTES.md` e mapa.
- [ ] Skill `preparar-space` criada e aplicada a cada projeto.
- [ ] Vigia de retomada no crontab; todo space com `CONTINUIDADE.md`.
- [ ] Graphify em cada projeto; vault Obsidian gerado com `--skip-graphify`.
- [ ] Fluxo de apps e regras de segurança nos `CLAUDE.md`.
- [ ] Fases opcionais (8, 11, 12) feitas ou recusadas pelo usuário, anotado.
Ao terminar, faça uma verificação independente (subagente verifier/explore em Sonnet, só leitura) e entregue ao
usuário um resumo curto do que ficou pronto e de como usar no dia a dia (“fale com o space diretrizes”).
