# Cluster slots without AI

Set `ORCHESTRA_CLUSTERS` to a copy of `clusters.example.json`. Names are arbitrary configuration keys. Each `measure_command` is a trusted local argv adapter that performs read-only measurement, optionally through SSH/PBS/Slurm, and prints JSON: `timestamp` (epoch seconds), `used_cores`, `used_memory_gb`, `load`, `jobs`. It must measure all users, not just the requesting user. No hosts, credentials, scheduler-specific project paths or remote commands are bundled. Configure per-cluster total, load, job-count and per-job resource limits.

```
pedir_vaga sample-alpha batch 2 4 sample-job "ready input"
pedir_vaga --lote sample-alpha requests.txt
pedir_vaga --listar
pedir_vaga --cancelar sample-alpha sample-job
checar_clusters --dry-run
registrar_job sample-alpha batch scheduler-id sample-job 2
registrar_job --ultimos 10
```

Batch lines: `cluster|cores|memory_GB|job_name|description`. Every line is validated before writing. Requests, cancellations, grants and registrations share a lock. Idle/done agents are mapped by their project directory basename. Priority is configured, never based on research names. No request means no wake-up. Closed/working agents leave requests pending. Successful grants consume the measured budget and a persistent lease until registration or expiry; set `lease_seconds` long enough for launch. Registration appends metadata and clears matching leases; the next measurement must include launched work. Reservations may temporarily double-count a launched-but-unregistered job, conservatively reducing capacity.

Stale or invalid measurements grant nothing. Persistent inaccessibility can notify only the configured coordinator after `unreachable_seconds`, limited by `repeat_seconds`; economy mode suppresses such notifications. `--dry-run` sends nothing and changes no queues/leases/health records. The checker never submits or kills a job. Site-specific overload/ownership alerts must be implemented in the read-only adapter or a separate watcher: research-specific kill policies were deliberately excluded.
