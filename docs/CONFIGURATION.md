# Adapt the kit to your environment

[Português brasileiro](CONFIGURATION.pt-BR.md)

All workspace names, SSH aliases and project identifiers in examples are fictitious. Select your own project directories, responsible people or teams, installed tools and resource budgets. A coordinator, multiple agents and MGE-LocalCompute are optional; a single project can use the bundled harness alone. See the [README](../README.md) for CLI environment variables.

Bootstrap input `language` is configurable (`en` by default; for example `pt-BR`). Classification follows that setting; existing upstream CLI messages and command identifiers retain their original language.

## Project policy

`orquestra/templates/project.yaml` preserves Portuguese keys for compatibility. Fields under `notes:` are instructions for agents. The optional credit-cycle and cluster tools use their own configuration; see [Credits](../orquestra/docs/CREDITS.md) and [Clusters](../orquestra/docs/CLUSTERS.md).

| Field under `notes:` | Meaning / suggested default |
|---|---|
| `dono` | Responsible person or team; replace `<responsavel>` |
| `maquina_mestre` | Main execution host or environment; replace `<host>` |
| `prioridade` | Project priority: `normal` or `alta` (high) |
| `creditos.perfil` | Local cost policy, initially `economico` (economical); select your own model/provider order |
| `creditos.trava` | Suggested pause fraction, `0.80`; choose a usage window and measurement source |
| `creditos.noite_pode_zerar` | Whether unattended work may exhaust the budget, `false`; availability comes from `modo`, not a fixed schedule |
| `servidores.usa`, `servidores.cotas` | Server aliases and resource quotas, `[]` and `{}`; no built-in cluster, CPU or temperature limits |
| `servidores.so_leitura` | Read-only server access, `false`; actual permissions remain controlled by the harness and server |
| `dados_sensiveis` | Sensitive-data flag, `false`; set `true` and restrict providers when applicable |
| `git.remoto`, `git.versoes` | Your repository identifier and local version labels |
| `autonomia.overrides` | Project-specific adjustments to the autonomy examples, `{}` |

`policy.plan_gate_paths: []` adds no project-specific files to the standard preapproval paths. To allow local working notes, set `policy.plan_gate_paths: ["notes/**"]` and recompile. This authorizes edits before plan approval, so use narrow paths. Immutable and protected paths still apply. Existing projects retain their copied `.uah/` implementation until they deliberately adopt the updated runtime; recompilation alone does not upgrade it.

## Global Bash guard

Installing the hook is an explicit setup step. No host, service, repository prefix or owner receives an external-action exception by default. Denials take precedence over exceptions. The guard is a command heuristic, not a security sandbox.

| Environment variable | Default / effect |
|---|---|
| `GUARD_HOSTS` | Unset: recursive remote removal is denied for all SSH hosts. Optional literal aliases separated by `|` restrict that denial to those hosts; this grants no copy permission |
| `GUARD_PROTECTED_RE` | Unset: no installation-specific protected path. Optional regex denies commands mentioning your protected resources |
| `GUARD_PROJECTS_BASE` | Unset: push asks for confirmation. Setting a root explicitly authorizes `git push [-q] [-u] origin <branch> [--tags]` within that root; symlinks are resolved and adjacent roots do not match |
| `GUARD_ALLOW_RULES` | `{}`: no routine exceptions. JSON object from ASK rule IDs to lists of regexes matching the entire command |
| `GUARD_LOG` | `~/.claude/hooks/guard-global/guard.log`; create its parent directory to enable logging. Commands may contain private data; keep this log local |
| `GUARD_GLOBAL_DISABLE` | Unset; `1` disables the global hook |

Example of a narrow, previously authorized routine (replace the fictitious destination):

```bash
export GUARD_ALLOW_RULES='{"H0-remote-copy":["scp result[.]txt example-cluster:incoming/result[.]txt"]}'
```

This does not authorize any other command, host or file. HTTPS notifications and model uploads still require their own explicit authorization. Configure H2/H3 grants separately when the project harness is also enabled; the global hook cannot override its restrictions.

## Availability, tools and quiet hours

Choose the tabs and models you actually use; names such as `claude`, `codex` and `opencode` are examples. The supplied watcher/resumer currently targets Claude agents; other kinds need an adapter. `modo` records present/away status without scheduling it. The coordinator is an optional agent following a template, not a built-in messaging service.

`ORCHESTRA_NIGHT_START=21` and `ORCHESTRA_NIGHT_END=8` are configurable notification defaults in the system local timezone, independent of presence mode. Values must be integer hours from 0 to 23. Equal values disable quiet hours; both same-day and midnight-crossing windows are supported. The optional credit-cycle tools have configurable day/night budgets; see [Credits](../orquestra/docs/CREDITS.md). Compute quotas are configured locally.

`git_v1.sh <project>` creates a local `v1` snapshot. Its default file-size threshold is 20 MiB (`GIT_V1_MAX_SIZE=20M`, GNU `find -size` syntax). It excludes likely secrets, environments and large scientific/media files; review the generated ignore list for your domain. `ARQUIVOS_FORA_DO_GIT.txt` means “files outside Git.”
