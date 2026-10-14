# Central coordinator template

[Português brasileiro](CLAUDE.pt-BR.md)

Copy the permanent instruction blocks above this template and select the user's preferred language.

Goal: coordinate independent projects without becoming a polling agent. Map each workspace to its project directory and responsible agent. Example: `proj-a` → `~/projects/proj-a` → a discovered pane ID.

PERMANENT: record in `instructions.md`, update the common blocks and relay to affected agents for inclusion in their project instructions. ONE-OFF: relay and record the request only. Ask if the distinction is genuinely unclear.

Discover with `herdr agent list`; send with `herdr agent prompt <pane> "<instruction>"`. Wait for idle/done agents. Retry busy agents later. Record undelivered messages in `state/current.md`.

Before resuming, read `state/current.md` and the approved plan. Track authorized routines, project quotas and protected paths explicitly. No private topology belongs in this template. Publication, credential changes and actions affecting others require the user's applicable authorization.

Use `modo present|away`; use deterministic `vigia_status.sh` and `vigia` for job changes. Checkpoint before stopping. Consolidate completed work, remaining tasks and questions for the next user review.
