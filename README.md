# UAH-Orquestra

*[Versão em português](README.pt-BR.md)*

**UAH-Orquestra is an adaptation of the [Universal Agent Harness (UAH)](https://github.com/fatioleg/Universal-Agent-Harness), created by Prof. Valter Carvalho-Silva (repository `fatioleg/Universal-Agent-Harness`).** The original defines how to configure and supervise *one* project run by AI agents (Claude Code, Codex): permissions, plan approval and resumable state. This adaptation, maintained by Mario Envall, adds **orchestration of several projects at once**: a central coordinating agent, the herdr terminal multiplexer, credit budgeting and continuous (overnight) work.

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
| **Machine capacity check** (`orquestra/bin/capacidade_pc`) | OK / TIGHT / FULL verdict before opening auxiliary AI sessions. |
| **Setup guide** (`docs/MONTAR_ARQUITETURA_CLAUDE.md`) | A phased guide for a Claude agent to build the architecture from scratch, skipping phases already done. |

## Changes to UAH-lite (`uah-lite/skills/uah-init/profiles/h0.json`)
- `git push`, remote `scp`/`rsync` and `curl` uploads are no longer "ask" in H0. They moved to the global guard, which allows only authorized destinations (the project's own repositories, the user's servers, the notification service) and asks for everything else.
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

> Note: the scripts, templates and `AUTONOMIA_E_MODOS.md` are written in Portuguese, as used day to day by the maintainer.

## Credits and license
- Original: **Universal Agent Harness**, by Prof. Valter Carvalho-Silva and contributors, MIT license. https://github.com/fatioleg/Universal-Agent-Harness
- Adaptation: Mario Envall (2026), same MIT license. See `LICENSE`.
