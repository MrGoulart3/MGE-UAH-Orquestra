# Deterministic job watcher

[Português brasileiro](VIGIA.pt-BR.md)

Create executable `vigia_status.sh` in each direct child of `ORCHESTRA_PROJECTS`. It runs locally with that directory as cwd; it must be trusted, short and read only. The watcher skips project/script symlinks, applies a timeout (default 300 seconds), retains the last 40 output lines, and wakes only idle/done Claude agents with the exact project cwd.

Print stable summary lines. Prefix discrete events with `!`; once event mode is seen, progress-only changes stop triggering prompts. Do not print current timestamps or continually changing load values. Example:

```sh
#!/bin/sh
if test -f result.status; then
    printf '! Calculation complete: %s\n' "$(cat result.status)"
else
    printf 'Running\n'
fi
```

Connectivity errors and nonzero exits must persist for `ORCHESTRA_FAILURE_SAMPLES` samples (default 3). A successful prompt sets the baseline; busy agents and failed prompts are retried on later invocations. `ORCHESTRA_WATCH_INTERVAL` defaults to 3600 seconds; new failure/error/stopped events bypass it. Logs of progress and baselines live only in `ORCHESTRA_STATE`. `vigia --dry-run` prints proposed prompts without accepting a new baseline. Cron example: `*/30 * * * * /absolute/checkout/orquestra/bin/vigia`. Supply environment variables in the crontab or a private launcher.
