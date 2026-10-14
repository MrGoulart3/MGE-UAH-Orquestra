# Autonomy and modes

[Português brasileiro](AUTONOMIA_E_MODOS.pt-BR.md)

`modo` stores present/away in `ORCHESTRA_STATE/mode.json`. Only the coordinating agent changes it on the user's instruction. Mode never grants permissions: away mode continues only an approved plan or explicitly authorized routines. New decisions go into `state/current.md` for the next review. Existing harness approval gates remain in force.

| Level | Behavior |
|---|---|
| L0 | Suggest; human decides |
| L1 | Execute after approval |
| L2 | Execute and validate |
| L3 | Execute, validate and correct once |
| L4 | Execute, correct and update project state |
| L5 | Complete the authorized workflow autonomously |

Default examples: reading L4; new project files L3; edits L2; protected files L1; deletion L0; declared tests L3; installation L1; publication L0–L1. Shared compute uses project-specific quotas; another person's files or processes are outside scope. No routine publication permission is implicit.

Prefer deterministic tools for monitoring, inexpensive models for nonsensitive simple work, implementation agents for code, and an independent check for scientific decisions. Keep secondary sessions closed when idle; consult MGE-LocalCompute before opening more sessions. Checkpoint before credit exhaustion or context changes. Resume only approved pending work; no pending work means remain idle.
