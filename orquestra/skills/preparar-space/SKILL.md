---
name: preparar-space
description: Prepare a new project workspace with generic multi-agent instructions, checkpoints and optional UAH orchestration.
---

# Prepare a project workspace

[Português brasileiro](SKILL.pt-BR.md)

1. Resolve the project root, goal, language and workspace name with the user. Preserve existing files. Inspect `herdr --help`, workspace and tab commands in the installed version; select tabs by name and discover pane IDs.
2. Prepare named tabs `claude`, `codex`, `opencode` with the same project cwd. Use unique agent names. Start only needed agents with `herdr agent start <unique-name> --kind <kind> --pane <pane>`. Resume an existing session only when its history exists. Obtain any required folder/hook trust from the user.
3. Build a short project `CLAUDE.md` from the shared blocks in `orquestra/templates/BLOCOS_PERMANENTES.md`: goal, current state, delegation policy, central coordinator and project restrictions. Reference private server rules locally; never copy credential files or private operational documents into a public project.
4. Create `state/current.md`: completed work, pending tasks, running job IDs and next step. Optionally keep `state/current.json` with `{"running": false}` for the idle-session utility; maintain it when launching or completing jobs.
5. Prepare `.graphifyignore` before optional graph indexing: environments, build directories, secrets, large logs and media. Verify installed integrations and provenance; do not auto-install unrelated tools.
6. If using UAH, fill `project.yaml`, initialize and compile with the bundled harness. Respect existing approval gates and the user's authorized scope. A new workspace alone does not authorize new computations, publication or global configuration changes.
7. For long tasks, create a deterministic `vigia_status.sh` with stable event lines, finite timeouts and terminal statuses. Record project resource quotas and use MGE-LocalCompute for local admission.
8. Register the workspace in the central map within the authorized scope. Validate named tabs, cwd, instructions, checkpoint, harness preflight and any optional integrations. Record PASS/FAIL and evidence; an independent read-only review may be used when appropriate.

## Current integration

Configure coordinator, exclusions and paths using the example file. Check cache/meter and the hook without model calls. Test a busy-agent message, cluster reservations with a fake adapter, and restart cancellation. Prepare continuity, handoff and delivery folders. Install cron/timers only when explicitly requested; keep compute and credit queues separate. Follow `orquestra/docs/`.
