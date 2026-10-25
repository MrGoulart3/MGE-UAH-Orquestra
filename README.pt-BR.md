# MGE-UAH-Orquestra

[![CI](https://github.com/MrGoulart3/MGE-UAH-Orquestra/actions/workflows/ci.yml/badge.svg?branch=ci)](https://github.com/MrGoulart3/MGE-UAH-Orquestra/actions/workflows/ci.yml) · [Changelog](CHANGELOG.md)

O badge exibirá status após a publicação da branch `ci`. / The badge shows status after the `ci` branch is published.

[Verificação local / Local checks](.github/CONTRIBUTING.md)

*[English version](README.md)*

**UAH-Orquestra é uma adaptação do [Universal Agent Harness (UAH)](https://github.com/fatioleg/Universal-Agent-Harness), criado pelos colaboradores do projeto original.** O original define como configurar e fiscalizar *um* projeto com agentes de IA (Claude Code, Codex): permissões, aprovação de plano e estado retomável. Esta adaptação junta isso a uma **orquestração de vários projetos ao mesmo tempo**, com um space central, o terminal herdr, economia de créditos e trabalho contínuo.

O código do UAH-lite em `uah-lite/` é uma cópia do original na versão 0.9.0 (commit `d26b183`) com pequenas alterações descritas abaixo. A licença MIT original foi mantida.

## O que vem do UAH original
- `project.yaml` (configuração H2), `plan/approved.md` com **aprovação humana travada por hash** (gate G1) e `state/current.md`.
- Proibições e confirmações **compiladas** em permissões e hooks do Claude Code (`uah.py compile`), com níveis de risco low, medium e high.
- Níveis de autonomia L0–L5 por tipo de ação e princípios como preservar fontes, checagens determinísticas primeiro e revisão independente.
- Catálogo de integrações: Workflow_Digestion, publish-documents, CalcBoard, sci-figures, specboard (todas do mesmo autor).

## O que esta adaptação acrescenta
| Peça | O que faz |
|---|---|
| **Space central ("diretrizes")** | Um agente coordena os demais: recebe ordens do usuário, classifica como PERMANENTE ou PONTUAL, registra e repassa a todos via `herdr agent prompt`. Cada projeto continua com o seu UAH-lite. |
| **Modo PRESENTE / AUSENTE** (`orquestra/bin/modo`) | Presente: plano aprovado antes de alterar, dúvidas na hora. Ausente (noite/fora): só executa o que já foi aprovado e as ações L3+; o resto fica para a manhã. A decisão é sempre do usuário. |
| **Autonomia padronizada** (`orquestra/AUTONOMIA_E_MODOS.md`) | Uma tabela L0–L5 única para todos os projetos, ajustável por projeto. |
| **Economia de créditos** | Escada grátis (opencode/groq/OpenRouter) → Codex → Claude. Trava em 80% do medidor de 5 h. À noite, sem projeto prioritário, pode zerar, porque um vigia sem IA retoma quando os créditos voltam (`orquestra/bin/retomar_apos_limite.sh`). |
| **Guarda global** (`orquestra/hooks/guard.py`) | Hook PreToolUse válido para todos os projetos, com as proibições H0 do UAH, regras de servidores compartilhados (matar só por PID, nada de `rm -r` remoto) e exceções configuráveis para rotinas já autorizadas. Teste com `python3 guard.py --test`. |
| **`project.yaml` estendido** | Campos de orquestração dentro de `notes:` (o `uah.py` só aceita extras ali): dono, máquina principal, prioridade, créditos, servidores e cotas, dados sensíveis, repositório git. |
| **Versões git por etapa** (`orquestra/bin/git_v1.sh`) | Repositório local e commit/tag `v1` sem segredos e sem arquivos grandes (que ficam listados); depois `v2`… |
| **Capacidade da máquina** (`orquestra/bin/capacidade_pc`) | Veredito OK / APERTADO / LOTADO antes de abrir IAs auxiliares. |
| **Roteiro de montagem** (`docs/MONTAR_ARQUITETURA_CLAUDE.md`) | Guia em fases para um Claude montar a arquitetura do zero, pulando as fases já feitas. |

## Alterações no UAH-lite (`uah-lite/skills/uah-init/profiles/h0.json`)
- H0 mantém confirmação explícita para `git push`, `scp`/`rsync` remoto e envio HTTP. Grants restritos do projeto podem autorizar rotinas individuais; o guard global acrescenta restrições de orquestração.
- `plan_gate_paths` ganhou `CONTINUIDADE.md`, `PENDENTES_CALC.md`, `_para_notebook/**`, `graphify-out/**` e `REGISTRO_CORRECOES.md`, para o estado e as notas poderem ser atualizados antes da aprovação.

## Uso rápido
```bash
cp orquestra/templates/project.yaml <projeto>/      # preencha
python3 uah-lite/skills/uah-init/uah.py --root <projeto> init --risk medium --project-id <id>
python3 <projeto>/.uah/uah.py compile               # sem BLOQUEADO
# escreva <projeto>/plan/approved.md (precisa de "## Escopo" e "pronto quando"/aceite)
python3 <projeto>/.uah/uah.py approve --by <você>    # decisão humana
```
Registre o guarda global em `~/.claude/settings.json` (PreToolUse, matcher `Bash`) e configure `GUARD_HOSTS` (aliases SSH confiáveis) e `GUARD_PROJECTS_BASE` (pasta dos projetos).

## Créditos e licença
- Original: **Universal Agent Harness**, de colaboradores do projeto original, licença MIT. https://github.com/fatioleg/Universal-Agent-Harness
- Adaptação: 2026, mesma licença MIT. Veja `LICENSE`.

## Kit genérico de orquestração

Python 3.10+ e Bash; as novas ferramentas não precisam de pacotes Python. Inclua `orquestra/bin/` no `PATH` e mantenha o checkout inteiro. Clonar não instala ferramentas, altera cron, envia prompts ou notificações. O kit usa o envelope JSON `result.agents` de `herdr agent list`; confira a compatibilidade com a versão instalada antes de automatizar.

```bash
export ORCHESTRA_PROJECTS="$HOME/projects"
export ORCHESTRA_STATE="$HOME/.local/state/mge-orchestra"
export MGE_LANG=pt-BR                    # ou en
export PATH="$PWD/orquestra/bin:$PATH"
modo presente
vigia --dry-run
retomar_apos_limite.sh todos nunca --once --dry-run
claudes_ociosos                         # relatório; --fechar envia /exit
pn-lista
printf 'proj-a|docs/result.md\n' | pn-arquiva lote-a
```

| Configuração | Padrão / função |
|---|---|
| `HERDR_BIN` | `herdr`; caminho do executável, sem comando shell |
| `ORCHESTRA_PROJECTS`, `ORCHESTRA_STATE` | `~/projects`, `~/.local/state/mge-orchestra` |
| `ORCHESTRA_NIGHT_START`, `ORCHESTRA_NIGHT_END` | 21, 8; fuso local do sistema |
| `NTFY_SERVER`, `NTFY_TOPIC`, `NTFY_TOKEN` | servidor `https://ntfy.sh`; tópico obrigatório para `avisar`; token opcional via ambiente |
| `GROQ_API_KEY`, `GROQ_MODEL` | ambos obrigatórios; escolha modelo disponível no provedor, sem leitura de arquivo de credenciais |
| `ORCHESTRA_IDLE_HOURS`, `ORCHESTRA_EXCLUDE` | 12; IDs de pane/workspace protegidos separados por vírgula |
| `ORCHESTRA_TRANSCRIPTS` | `~/.claude/projects`; consulta só mtime, nunca conteúdo de transcrições |
| `ORCHESTRA_HANDOFF` | `_handoff`; `pn-arquiva` move arquivos recebidos para `.sent/<lote>/` |
| `ORCHESTRA_JOB_STATE` | Registro JSON do MGE-LocalCompute; jobs locais ativos protegem as sessões do projeto. |
| `LOCALCOMPUTE_HOME` | checkout irmão usado por `capacidade_pc` |

`avisar "Título" "Mensagem" [alta]` força prioridade baixa à noite, inclusive em urgência. Credenciais vêm apenas do ambiente. `groq [-m modelo] "pergunta" < sintetico.txt` limita o contexto de stdin a 12.000 caracteres; não envie dados privados. Ferramentas não registram chaves de API nem corpos de erros HTTP.

`claudes_ociosos` só considera sessões com mtime antigo conhecido, estado ocioso confirmado, sem vigia e `state/current.json` explicitamente com `{"running": false}`. Falta de evidência mantém a sessão. Esse estado deve incluir todos os jobs locais ou remotos. `--fechar` é explícito; a ferramenta reconfirma o estado antes de `/exit`.

A retomada verifica só as últimas dez linhas não vazias da tela para avisos de limite; tenta a cada 600 segundos (`ORCHESTRA_RESUME_INTERVAL`). Depende do texto da interface e não prova que os créditos voltaram. Escolha alvo ou `todos`, prazo local `HH:MM` ou `nunca` e mensagem opcional. Use serviço ou chamada agendada única, sem instâncias sobrepostas. Detalhes: [VIGIA](docs/VIGIA.pt-BR.md). Modelos: [blocos permanentes](orquestra/templates/BLOCOS_PERMANENTES.pt-BR.md), [central](orquestra/templates/CLAUDE.pt-BR.md), [autonomia](orquestra/AUTONOMIA_E_MODOS.pt-BR.md), [skill preparar-space](orquestra/skills/preparar-space/SKILL.pt-BR.md). Harness e créditos de terceiros permanecem em `uah-lite/`.

Validação: `python3 -m unittest discover -s orquestra/tests -v`; `python3 orquestra/hooks/guard.py --test`; `python3 -m unittest discover -s uah-lite/tests -v` (a última requer dependências de desenvolvimento do original).

## Relacionados

- [MGE-AgentPortal](https://github.com/MrGoulart3/MGE-AgentPortal): acesso autenticado aos workspaces e painel opcional de recursos.
- [MGE-LocalCompute](https://github.com/MrGoulart3/MGE-LocalCompute): admissão de recursos compartilhados, fila noturna e guarda térmica em degraus.


## Como as peças se conectam

O medidor alimenta a trava de créditos e a porta da manhã. Vigias guardam recados até o agente parar. Cálculos prontos pedem vagas por arquivo; apenas concessões confirmadas avisam o agente. Reinícios gravam a passagem de contexto antes. Otimização e prioridade noturnas têm filas separadas. LocalCompute cuida da admissão e proteção dos processos; AgentPortal chama os scripts de sessão e mostra as pastas de entrega configuradas.

| Sistema | Comandos | Guia |
|---|---|---|
| Créditos | `medidor`, `trava_creditos`, `trava_excecao` | [Créditos](orquestra/docs/CREDITS.md) |
| Ciclo matutino | `ciclo`, `ciclo_controle`, `ciclo_porta_hook`, `ancora_reserva`, `ancorar_janela`, `acordar_manha` | [Ciclo](orquestra/docs/CICLO_MATUTINO.md) |
| Recados | `enviar_space`, `entregar_pendentes`, `pane_coordenador` | [Recados](orquestra/docs/MESSAGES.md) |
| Vagas em clusters | `pedir_vaga`, `checar_clusters`, `registrar_job` | [Clusters](orquestra/docs/CLUSTERS.md) |
| Contexto e sessões | `contexto_spaces`, `passagem_space`, `reiniciar_space`, `custo_sessoes`, `fechar_space`, `acordar_space` | [Reinício](orquestra/docs/REINICIO_SPACES.md) |
| Filas noturnas | `otimizacao_noturna`, `fila_prioridade_noite` | [Otimização](orquestra/docs/OTIMIZACAO_NOTURNA.md) |
| Arquivos e links | `deliver_file`, `central_add` | [Entregas](orquestra/docs/DELIVERIES.md) |
| Economia e resumo | `modo_economia`, `resumo_manha` | [Economia](orquestra/docs/ECONOMY_AND_SUMMARY.md) |

Copie `orquestra/config.example.sh` para um arquivo local confiável e exporte seu caminho absoluto em `ORCHESTRA_CONFIG`. Configuração e estado ficam fora do Git. Adicione `orquestra/bin` ao PATH; os comandos precisam do arquivo de ambiente, módulos Python e `ciclo_core.mjs`. Configure coordenador e adaptadores antes de instalar cron/hooks manualmente. O repositório não altera serviços, agendamentos nem jobs remotos. O ping da manhã precisa ser habilitado na configuração. Valide sem rede com `python .github/scripts/check.py`. Os guias por sistema estão em inglês.
