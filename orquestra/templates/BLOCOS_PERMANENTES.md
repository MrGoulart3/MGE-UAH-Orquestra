# Shared permanent instructions

[Português brasileiro](BLOCOS_PERMANENTES.pt-BR.md)

> Workspace `<project-name>` uses named tabs for the selected tools (for example `claude`, `codex`, `opencode`); discover pane IDs rather than relying on tab order.
> Read `state/current.md` before resuming; record completed work, running job identifiers, pending questions and the next action before stopping.
> Prefer deterministic status scripts. Delegate only nonsensitive simple tasks to inexpensive models; verify numbers independently.
> Apply the project's resource admission policy; MGE-LocalCompute is an optional implementation. Never bypass configured admission checks or modify another person's process.
> Keep secondary interactive sessions closed when idle. Use short commands when practical.
> If a coordinating agent is enabled, it distinguishes PERMANENT instructions from ONE-OFF requests, maintains this source and relays changes without interrupting working agents.
> Preserve original data. Never include secrets, private addresses or unpublished results in public repositories, model requests or push notifications.
> Use `deliver_file` for Portal deliveries; legacy acknowledged transfers can still use `_handoff/`. Notifications use configured ntfy and remain silent during the configured night window.
> Presence mode does not change authorization. Away mode continues approved work and records new decisions for review.
> If a genuine ambiguity changes the result, ask before dependent work.

> **2026-10-24 update:** send ordinary messages with `enviar_space` and wait for idle; reserve `URGENTE=1` for protection/lifecycle. Credits default to day 75/80, night 90/95 and morning cap 30%; enforce the door through its hook, with explicit temporary exceptions. Ready jobs use `pedir_vaga`, then `registrar_job` after launch, without coordinator replies. Cheap restart saves a handoff; cancellation persists until release. Use `deliver_file` for files and `central_add` for links. All lightweight computation uses LocalCompute with one registry and RAM protection. See system guides in `docs/`; configure priorities and machines locally.
