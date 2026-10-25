# MGE-UAH-Orquestra

[![CI](https://github.com/MrGoulart3/MGE-UAH-Orquestra/actions/workflows/ci.yml/badge.svg?branch=ci)](https://github.com/MrGoulart3/MGE-UAH-Orquestra/actions/workflows/ci.yml) · [Changelog](CHANGELOG.md)

O badge exibirá status após a publicação da branch `ci`. / The badge shows status after the `ci` branch is published.

[Verificação local / Local checks](.github/CONTRIBUTING.md)

*[Versão em português](README.pt-BR.md)*

**UAH-Orquestra is an adaptation of the [Universal Agent Harness (UAH)](https://github.com/fatioleg/Universal-Agent-Harness), created by the upstream contributors.** The original defines how to configure and supervise *one* project run by AI agents (Claude Code, Codex): permissions, plan approval and resumable state. This adaptation adds **orchestration of several projects at once**: a central coordinating agent, the herdr terminal multiplexer, credit budgeting and continuous (overnight) work.

The UAH-lite code in `uah-lite/` is a copy of the original at version 0.9.0 (commit `d26b183`), with the small changes listed below. The original MIT license is kept.

## What comes from the original UAH
- `project.yaml` (H2 configuration), `plan/approved.md` with **human approval locked by hash** (gate G1), and `state/current.md`.
- Prohibitions and confirmations **compiled** into Claude Code permissions and hooks (`uah.py compile`), with low, medium and high risk levels.
- Autonomy levels L0–L5 per type of action, and principles such as preserving sources, deterministic checks first and independent review.
- Integration catalog: Workflow_Digestion, publish-documents, CalcBoard, sci-figures, specboard (all by the same author).

## What this adaptation adds
| Component | What it does |
|---|---|
| **Central agent ("diretrizes")** | One agent coordinates the others: it receives the user's instructions, classifies them as PERMANENT or ONE-OFF, logs them and relays them to every project via `herdr agent prompt`. Each project keeps its own UAH-lite. |
| **PRESENT / AWAY mode** (`orquestra/bin/modo`) | Present: plans are approved before any change and questions are asked right away. Away (night/out): agents only run what was already approved plus L3+ actions; everything else waits for the morning. The decision always stays with the user. |
| **Standardized autonomy** (`orquestra/AUTONOMIA_E_MODOS.md`) | A single L0–L5 table shared by all projects, adjustable per project. |
| **Credit budgeting** | A cost ladder: free models (opencode/Groq/OpenRouter) → Codex → Claude. Work pauses at 80% of the 5-hour usage meter. At night, with no priority project, credits may run out, because a non-AI watcher resumes the agents when credits return (`orquestra/bin/retomar_apos_limite.sh`). |
| **Global guard** (`orquestra/hooks/guard.py`) | A PreToolUse hook valid for every project: the UAH H0 prohibitions, rules for shared compute servers (kill only by PID, no remote `rm -r`) and configurable exceptions for already-authorized routines. Test with `python3 guard.py --test`. |
| **Extended `project.yaml`** | Orchestration fields inside `notes:` (the only place `uah.py` accepts extra keys): owner, main machine, priority, credits, servers and quotas, sensitive data, git repository. |
| **Git versions per stage** (`orquestra/bin/git_v1.sh`) | Local repository plus commit/tag `v1`, excluding secrets and large files (which are listed instead); then `v2`, and so on. |
| **Machine capacity check** (`orquestra/bin/capacidade_pc`) | Delegates to MGE-LocalCompute through `LOCALCOMPUTE_HOME`. |
| **Setup guide** (`docs/MONTAR_ARQUITETURA_CLAUDE.md`) | A phased guide for a Claude agent to build the architecture from scratch, skipping phases already done. |

## Changes to UAH-lite (`uah-lite/skills/uah-init/profiles/h0.json`)
- H0 keeps explicit confirmation rules for `git push`, remote `scp`/`rsync` and HTTP uploads. Narrow project grants can authorize individual routines; the global guard adds orchestration restrictions.
- `plan_gate_paths` now includes `CONTINUIDADE.md`, `PENDENTES_CALC.md`, `_para_notebook/**`, `graphify-out/**` and `REGISTRO_CORRECOES.md`, so state files and notes can be updated before a plan is approved.

## Quick start
```bash
cp orquestra/templates/project.yaml <project>/      # fill it in
python3 uah-lite/skills/uah-init/uah.py --root <project> init --risk medium --project-id <id>
python3 <project>/.uah/uah.py compile               # must finish without BLOQUEADO (blocked)
# write <project>/plan/approved.md (it needs "## Escopo" (scope) and acceptance criteria)
python3 <project>/.uah/uah.py approve --by <you>    # human decision
```
Register the global guard in `~/.claude/settings.json` (PreToolUse, matcher `Bash`) and set `GUARD_HOSTS` (trusted SSH aliases) and `GUARD_PROJECTS_BASE` (projects folder).

> Note: the new CLI utilities select English or Portuguese with `MGE_LANG`; the upstream harness retains its own language conventions.

## Credits and license
- Original: **Universal Agent Harness**, by upstream contributors, MIT license. https://github.com/fatioleg/Universal-Agent-Harness
- Adaptation: 2026, same MIT license. See `LICENSE`.

## Generic orchestration kit

Python 3.10+ and Bash; the new utilities need no Python packages. Keep `orquestra/bin/` in `PATH` and the checkout intact. No installation, cron changes, agent prompts or notifications happen just by checking out this repository. The toolkit follows the `herdr agent list` JSON envelope `result.agents`; validate it against your installed herdr version before enabling automation.

```bash
export ORCHESTRA_PROJECTS="$HOME/projects"
export ORCHESTRA_STATE="$HOME/.local/state/mge-orchestra"
export MGE_LANG=en                       # or pt-BR
export PATH="$PWD/orquestra/bin:$PATH"
modo present                            # also accepts presente/ausente
vigia --dry-run
retomar_apos_limite.sh all never --once --dry-run
claudes_ociosos                         # report only; --close sends /exit
pn-lista
printf 'proj-a|docs/result.md\n' | pn-arquiva batch-a
```

| Setting | Default / purpose |
|---|---|
| `HERDR_BIN` | `herdr`; executable path, not a shell command |
| `ORCHESTRA_PROJECTS`, `ORCHESTRA_STATE` | `~/projects`, `~/.local/state/mge-orchestra` |
| `ORCHESTRA_NIGHT_START`, `ORCHESTRA_NIGHT_END` | 21, 8; system local timezone |
| `NTFY_SERVER`, `NTFY_TOPIC`, `NTFY_TOKEN` | server defaults to `https://ntfy.sh`; topic required for `avisar`; optional environment token |
| `GROQ_API_KEY`, `GROQ_MODEL` | both required; choose your provider-supported model, no credential file is read |
| `ORCHESTRA_IDLE_HOURS`, `ORCHESTRA_EXCLUDE` | 12; comma-separated protected pane/workspace IDs |
| `ORCHESTRA_TRANSCRIPTS` | `~/.claude/projects`; reads file mtime only, never transcript contents |
| `ORCHESTRA_HANDOFF` | `_handoff`; `pn-arquiva` moves acknowledged files under `.sent/<batch>/` |
| `ORCHESTRA_JOB_STATE` | MGE-LocalCompute JSON job registry; active local jobs protect their project sessions. |
| `LOCALCOMPUTE_HOME` | sibling checkout used by `capacidade_pc` |

`avisar "Title" "Message" [high]` forces low priority at night even for urgent requests. Only configured environment credentials are used. `groq [-m model] "question" < synthetic.txt` bounds stdin context to 12,000 characters; do not send private data. Utilities never log API keys or HTTP error bodies.

`claudes_ociosos` keeps sessions unless they have known old transcript mtimes, definite idle state, no watcher, and `state/current.json` explicitly containing `{"running": false}`. Missing evidence keeps the session. The state file must include every ongoing local or remote job. `--close` is opt-in; the utility rechecks agent state before `/exit`.

The resumer tests only the last ten nonempty screen lines for usage-limit text; it retries every 600 seconds (`ORCHESTRA_RESUME_INTERVAL`). This depends on the agent's display wording and does not prove credits have returned. Choose a target or `all`, a local `HH:MM` deadline or `never`, and optionally a custom message. Run as a service or scheduled one-shot, never overlapping instances. Watcher details: [VIGIA](docs/VIGIA.md). Generic instructions: [permanent blocks](orquestra/templates/BLOCOS_PERMANENTES.md), [central template](orquestra/templates/CLAUDE.md), [autonomy](orquestra/AUTONOMIA_E_MODOS.md), [prepare-space skill](orquestra/skills/preparar-space/SKILL.md). The upstream harness and its third-party credits remain under `uah-lite/`.

Validation: `python3 -m unittest discover -s orquestra/tests -v`; `python3 orquestra/hooks/guard.py --test`; `python3 -m unittest discover -s uah-lite/tests -v` (the latter requires the upstream development requirements).

## Related

- [MGE-AgentPortal](https://github.com/MrGoulart3/MGE-AgentPortal): authenticated workspace access and optional PC resources panel.
- [MGE-LocalCompute](https://github.com/MrGoulart3/MGE-LocalCompute): shared resource admission, nighttime queue and gradual thermal guard.


## How the pieces fit

The meter feeds credit protection and the morning door. Watchers queue notices until an agent is idle. Ready cluster work requests slots through files; only successful grants notify its agent. Context restarts save a handoff first. Night optimization and priority work are serialized separately. LocalCompute owns admission and process protection; AgentPortal invokes the lifecycle scripts and displays configured delivery folders.

| System | Commands | Guide |
|---|---|---|
| Credits | `medidor`, `trava_creditos`, `trava_excecao` | [Credits](orquestra/docs/CREDITS.md) |
| Morning cycle | `ciclo`, `ciclo_controle`, `ciclo_porta_hook`, `ancora_reserva`, `ancorar_janela`, `acordar_manha` | [Cycle](orquestra/docs/CICLO_MATUTINO.md) |
| Messages | `enviar_space`, `entregar_pendentes`, `pane_coordenador` | [Messages](orquestra/docs/MESSAGES.md) |
| Cluster slots | `pedir_vaga`, `checar_clusters`, `registrar_job` | [Clusters](orquestra/docs/CLUSTERS.md) |
| Context and lifecycle | `contexto_spaces`, `passagem_space`, `reiniciar_space`, `custo_sessoes`, `fechar_space`, `acordar_space` | [Restart](orquestra/docs/REINICIO_SPACES.md) |
| Night queues | `otimizacao_noturna`, `fila_prioridade_noite` | [Optimization](orquestra/docs/OTIMIZACAO_NOTURNA.md) |
| Files and links | `deliver_file`, `central_add` | [Delivery](orquestra/docs/DELIVERIES.md) |
| Economy and summary | `modo_economia`, `resumo_manha` | [Economy](orquestra/docs/ECONOMY_AND_SUMMARY.md) |

Copy `orquestra/config.example.sh` to a trusted local file and export `ORCHESTRA_CONFIG` to its absolute path. Keep configuration and runtime state out of Git. Add `orquestra/bin` to PATH. Do not copy individual wrappers without `orchestra-env.sh`, the Python modules and `ciclo_core.mjs`. Configure the coordinator and cluster adapters before installing cron/hooks manually. No schedules, settings, remote jobs or services are changed by this repository. The morning ping requires explicit configuration. Validate offline with `python .github/scripts/check.py`.
