"""File-based cluster requests and conservative grants without model calls."""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import orchestra


def settings() -> dict:
    """Reads operator-defined names, limits and read-only measurement commands."""
    return json.loads(Path(os.environ['ORCHESTRA_CLUSTERS']).expanduser().read_text())


def identifier(value: str) -> str:
    """Accepts a plain state key."""
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('Invalid identifier')
    return value


def request(space: str, fields: list[str], cfg: dict) -> dict:
    """Validates a single request before any state is written."""
    if len(fields) not in (4, 5):
        raise ValueError('Invalid request field count')
    cluster, cores, memory, name, *description = fields
    identifier(space)
    if cluster not in cfg['clusters'] or int(cores) < 1 or not math.isfinite(float(memory)) or float(memory) <= 0:
        raise ValueError('Invalid cluster resources')
    for value in [name, *description]:
        if any(char in value for char in '\n\r|'):
            raise ValueError('Invalid request field')
    if not name:
        raise ValueError('Job name is required')
    return dict(space=space, cluster=cluster, cores=int(cores), memory_gb=float(memory),
                name=name, description=description[0] if description else '', created=time.time())


def requests_path() -> Path:
    """Returns the shared queue file."""
    return orchestra.base() / 'cluster-requests.json'


def read_requests() -> list[dict]:
    """Reads the request queue while the caller holds the cluster lock."""
    path = requests_path()
    return json.loads(path.read_text()) if path.exists() else []


def measure(spec: dict) -> dict:
    """Runs a configured argv adapter; stale/invalid snapshots never grant slots."""
    command = spec['measure_command']
    if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        raise ValueError('measure_command must be an argv list')
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
    data = json.loads(result.stdout)
    for key in ('timestamp', 'used_cores', 'used_memory_gb', 'load', 'jobs'):
        value = data[key]
        if not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError('Invalid snapshot')
    if not 0 <= time.time() - data['timestamp'] <= spec.get('max_age_seconds', 1200):
        raise ValueError('Stale snapshot')
    return data


def grants(cfg: dict, dry: bool) -> None:
    """Reserves each successful grant in this round before checking the next."""
    with orchestra.lock('clusters'):
        state_path = orchestra.base() / 'clusters-health.json'
        health = json.loads(state_path.read_text()) if state_path.exists() else {}
        snapshots = {}
        now = time.time()
        economy = orchestra.base() / 'ECONOMIA_ATE'
        paused = economy.exists() and float(economy.read_text()) > now
        paused = paused or (orchestra.base() / 'PORTA_FECHADA').exists()
        for name, spec in cfg['clusters'].items():
            identifier(name)
            try:
                snapshots[name] = measure(spec)
                health[name] = {'failed_since': 0, 'alerted': 0}
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                old = health.setdefault(name, {'failed_since': now, 'alerted': 0})
                if not old['failed_since']:
                    old['failed_since'] = now
                if now - old['failed_since'] >= cfg.get('unreachable_seconds', 3600) and now - old['alerted'] >= cfg.get('repeat_seconds', 7200):
                    print(f'UNREACHABLE: {name}')
                    if not dry and not paused and os.environ.get('ORCHESTRA_COORDINATOR'):
                        delivered = send(os.environ['ORCHESTRA_COORDINATOR'], f'CLUSTER UNREACHABLE: {name}; inspect read-only measurements.')
                        if delivered:
                            old['alerted'] = now
        pool = {Path(a.get('cwd', '')).name: a for a in orchestra.agents() if orchestra.idle(a)}
        order = cfg.get('priority', [])
        pending = read_requests()
        pending.sort(key=lambda row: (order.index(row['space']) if row['space'] in order else len(order), row['created']))
        remaining = []
        leases_path = orchestra.base() / 'cluster-leases.json'
        leases = json.loads(leases_path.read_text()) if leases_path.exists() else []
        leases = [lease for lease in leases if lease['expires'] > now]
        # Grants remain reserved across cron rounds until registration or expiry.
        for lease in leases:
            data = snapshots.get(lease['cluster'])
            if data:
                data['used_cores'] += lease['cores']
                data['load'] += lease['cores']
                data['used_memory_gb'] += lease['memory_gb']
                data['jobs'] += 1
        for row in pending:
            spec = cfg['clusters'][row['cluster']]
            data = snapshots.get(row['cluster'])
            agent = pool.get(row['space'])
            fits = (data and agent and not paused
                    and data['used_cores'] + row['cores'] <= spec['max_cores']
                    and data['load'] + row['cores'] <= spec.get('max_load', spec['max_cores'])
                    and data['used_memory_gb'] + row['memory_gb'] <= spec['max_memory_gb']
                    and data['jobs'] < spec.get('max_jobs', 100000)
                    and row['cores'] <= spec.get('max_job_cores', spec['max_cores'])
                    and row['memory_gb'] <= spec.get('max_job_memory_gb', spec['max_memory_gb']))
            if fits:
                message = f"SLOT GRANTED: {row['cluster']} {row['cores']} cores for {row['name']}. Launch under cluster policy and run registrar_job; do not reply to the coordinator."
                if dry or send(agent['pane_id'], message):
                    print('DRYRUN' if dry else 'GRANTED', row['space'], row['name'])
                    data['used_cores'] += row['cores']
                    data['used_memory_gb'] += row['memory_gb']
                    data['load'] += row['cores']
                    data['jobs'] += 1
                    if not dry:
                        leases.append(row | {'expires': now + cfg.get('lease_seconds', 1800)})
                        with (orchestra.base() / 'cluster-grants.jsonl').open('a') as stream:
                            stream.write(json.dumps(row | {'granted': now}) + '\n')
                        continue
            remaining.append(row)
        if not dry:
            orchestra.save(requests_path(), remaining)
            orchestra.save(leases_path, leases)
            orchestra.save(state_path, health)


def send(pane: str, message: str) -> bool:
    """Does not enqueue grants that must be re-evaluated on the next round."""
    result = subprocess.run([str(Path(__file__).parent / 'bin/enviar_space'), pane, message, '0'],
                            env=os.environ | {'NAO_GUARDAR': '1'}, timeout=15, check=False)
    return result.returncode == 0


def main() -> int:
    """Dispatches file-only requests, grants and job registration."""
    parser = argparse.ArgumentParser()
    parser.add_argument('tool', choices=['pedir_vaga', 'checar_clusters', 'registrar_job'])
    parser.add_argument('args', nargs=argparse.REMAINDER)
    parsed = parser.parse_args()
    args = parsed.args
    try:
        if parsed.tool == 'checar_clusters':
            grants(settings(), '--dry-run' in args or os.environ.get('DRYRUN') == '1')
        elif parsed.tool == 'registrar_job':
            with orchestra.lock('clusters'):
                path = orchestra.base() / 'jobs.jsonl'
                if args and args[0] == '--ultimos':
                    print('\n'.join(path.read_text().splitlines()[-int(args[1] if len(args) > 1 else 10):]) if path.exists() else '')
                    return 0
                if len(args) not in (4, 5) or any(not a or any(c in a for c in '\n\r|') for a in args):
                    raise ValueError('Use space cluster id name [cores]')
                if len(args) == 5 and int(args[4]) < 1:
                    raise ValueError('Invalid cores')
                with path.open('a') as stream:
                    stream.write(json.dumps(dict(timestamp=time.time(), space=args[0], cluster=args[1], id=args[2], name=args[3], cores=int(args[4]) if len(args) > 4 else None)) + '\n')
                leases = orchestra.base() / 'cluster-leases.json'
                if leases.exists():
                    orchestra.save(leases, [r for r in json.loads(leases.read_text()) if (r['space'], r['cluster'], r['name']) != (args[0], args[1], args[3])])
        else:
            with orchestra.lock('clusters'):
                rows = read_requests()
                if args == ['--listar']:
                    print(json.dumps(rows, indent=2))
                    return 0
                if len(args) == 3 and args[0] == '--cancelar':
                    rows = [r for r in rows if (r['space'], r['name']) != (args[1], args[2])]
                elif len(args) == 3 and args[0] == '--lote':
                    cfg = settings()
                    additions = [request(args[1], line.split('|'), cfg) for line in Path(args[2]).read_text().splitlines() if line.strip() and not line.startswith('#')]
                    if not additions:
                        raise ValueError('Empty batch')
                    rows.extend(additions)
                elif len(args) in (5, 6):
                    rows.append(request(args[0], args[1:], settings()))
                else:
                    raise ValueError('Use space cluster cores memory_GB name [description]')
                orchestra.save(requests_path(), rows)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
