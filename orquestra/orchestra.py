#!/usr/bin/env python3
"""Configurable orchestration utilities; herdr calls always use argument vectors."""
from __future__ import annotations

import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request


def text(en: str, pt: str) -> str:
    """Selects the language used by CLI messages and agent prompts."""
    return pt if os.environ.get('MGE_LANG') == 'pt-BR' else en


def base() -> Path:
    """Creates private runtime state."""
    path = Path(os.environ.get('ORCHESTRA_STATE', '~/.local/state/mge-orchestra')).expanduser()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def projects() -> Path:
    """Returns the configured project root."""
    return Path(os.environ.get('ORCHESTRA_PROJECTS', '~/projects')).expanduser().resolve()


def save(path: Path, value: object) -> None:
    """Atomically saves JSON."""
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False))
    tmp.replace(path)


@contextlib.contextmanager
def lock(name: str):
    """Prevents overlapping cron invocations from issuing duplicate prompts."""
    with (base() / f'{name}.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def herdr(*args: str) -> str:
    """Calls the installed herdr executable with a finite timeout."""
    result = subprocess.run([os.environ.get('HERDR_BIN', 'herdr'), *args], check=True,
                            capture_output=True, text=True, timeout=30)
    return result.stdout


def agents() -> list[dict]:
    """Parses the same herdr result envelope used by the original utilities."""
    return json.loads(herdr('agent', 'list'))['result']['agents']


def prompt(agent: dict, message: str, dry_run: bool = False) -> None:
    """Sends only explicitly requested prompts; preview is side-effect free."""
    if dry_run:
        print(f'DRY RUN: {agent["pane_id"]}: {message}')
    else:
        subprocess.run([str(Path(__file__).parent / 'bin/enviar_space'),
                        agent['pane_id'], message, '0'],
                       env=os.environ | {'NAO_GUARDAR': '1'},
                       check=True, timeout=15)


def mode(value: str | None) -> None:
    """Reads or updates present/away mode without granting new permissions."""
    aliases = {'presente': 'present', 'ausente': 'away', 'present': 'present', 'away': 'away'}
    with lock('mode'):
        path = base() / 'mode.json'
        old = json.loads(path.read_text()) if path.exists() else 'present'
        if value is None:
            print({'present': 'presente', 'away': 'ausente'}[old] if os.environ.get('MGE_LANG') == 'pt-BR' else old)
            return
        if value not in aliases:
            raise ValueError('Use present|away / presente|ausente')
        new = aliases[value]
        save(path, new)
        with (base() / 'mode.log').open('a') as log:
            log.write(f'{datetime.datetime.now().isoformat()} {old} -> {new}\n')
        labels = {'present': 'presente', 'away': 'ausente'} if os.environ.get('MGE_LANG') == 'pt-BR' else {'present': 'present', 'away': 'away'}
        print(f'{labels[old]} -> {labels[new]}')
    if os.environ.get('NTFY_TOPIC'):
        notify(text('Mode', 'Modo'), f'{old} -> {new}', 'default')


def priority(requested: str, hour: int) -> str:
    """Forces silent priority during the configured night window."""
    start = int(os.environ.get('ORCHESTRA_NIGHT_START', '21'))
    end = int(os.environ.get('ORCHESTRA_NIGHT_END', '8'))
    if not (0 <= start <= 23 and 0 <= end <= 23):
        raise ValueError("Quiet hours must be 0–23 / Horários devem estar entre 0 e 23")
    night = start != end and (start <= hour < end if start < end else hour >= start or hour < end)
    return 'low' if night else ('high' if requested in ('high', 'alta') else 'default')


def notify(title: str, message: str, requested: str) -> None:
    """Posts a configured ntfy message without reading any credential files."""
    topic = os.environ.get('NTFY_TOPIC', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', topic):
        raise ValueError('Set NTFY_TOPIC / Configure NTFY_TOPIC')
    url = os.environ.get('NTFY_SERVER', 'https://ntfy.sh').rstrip('/') + '/' + topic
    headers = {'Title': title.encode('utf-8').decode('latin-1'),
               'Priority': priority(requested, datetime.datetime.now().hour)}
    if os.environ.get('NTFY_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['NTFY_TOKEN']
    request = urllib.request.Request(url, message.encode(), headers, method='POST')
    with urllib.request.urlopen(request, timeout=15) as response:
        print(response.status)


def groq(question: str, model: str | None, context: str) -> None:
    """Sends a bounded prompt using an environment-supplied key and model."""
    key = os.environ.get('GROQ_API_KEY')
    selected = model or os.environ.get('GROQ_MODEL')
    if not key or not selected:
        raise ValueError('Set GROQ_API_KEY and GROQ_MODEL / Configure GROQ_API_KEY e GROQ_MODEL')
    if len(context) > 12000:
        context = context[:4000] + '\n[truncated / cortado]\n' + context[-7977:]
    body = json.dumps({'model': selected, 'messages': [{'role': 'user', 'content': question + '\n\n' + context}], 'max_tokens': 900}).encode()
    request = urllib.request.Request('https://api.groq.com/openai/v1/chat/completions', body,
                                     {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=60) as response:
        print(json.load(response)['choices'][0]['message']['content'].strip())


def idle(agent: dict) -> bool:
    """Recognizes only definite idle states."""
    return agent.get('agent') == 'claude' and agent.get('agent_status') in ('idle', 'done')


def resume(target: str, until: str, message: str | None, once: bool, dry_run: bool) -> None:
    """Retries idle agents whose recent screen contains a usage-limit notice."""
    end = None
    if until not in ('never', 'nunca'):
        parsed = datetime.datetime.strptime(until, '%H:%M').time()
        end = datetime.datetime.combine(datetime.date.today(), parsed)
        if end <= datetime.datetime.now():
            end += datetime.timedelta(days=1)
    default = text('AUTOMATIC RESUME: read state/current.md and continue authorized pending tasks. If none, stay idle.',
                   'RETOMADA AUTOMÁTICA: leia state/current.md e continue as tarefas pendentes autorizadas. Sem pendências, fique ocioso.')
    with lock('resume'):
        while end is None or datetime.datetime.now() < end:
            for agent in agents():
                if not idle(agent) or (target not in ('all', 'todos') and target not in (agent.get('name'), agent.get('pane_id'))):
                    continue
                screen = '\n'.join(line for line in herdr('agent', 'read', agent['pane_id']).splitlines() if line.strip())
                if re.search(r'hit your (usage )?limit|limit reached|usage limit|resets \d{1,2}(:\d{2})?\s*(am|pm)', '\n'.join(screen.splitlines()[-10:]), re.I):
                    prompt(agent, message or default, dry_run)
                    with (base() / 'resume.log').open('a') as log:
                        log.write(f'{datetime.datetime.now().isoformat()} {agent["pane_id"]}\n')
            if once:
                break
            delay = float(os.environ.get('ORCHESTRA_RESUME_INTERVAL', '600'))
            if delay <= 0:
                raise ValueError('Resume interval must be positive / Intervalo deve ser positivo')
            if end:
                delay = min(delay, max(0, (end - datetime.datetime.now()).total_seconds()))
            time.sleep(delay)


def watcher(dry_run: bool = False) -> None:
    """Prompts idle project agents only after persistent, meaningful changes."""
    with lock('watcher'):
        path = base() / 'watcher.json'
        state = json.loads(path.read_text()) if path.exists() else {}
        pool = agents()
        for script in sorted(projects().glob('*/vigia_status.sh')):
            if script.parent.is_symlink() or script.is_symlink() or not os.access(script, os.X_OK):
                continue
            folder = str(script.parent.resolve())
            key = hashlib.sha256(folder.encode()).hexdigest()
            old = state.get(key, {'output': None, 'sent': 0, 'failures': 0})
            try:
                result = subprocess.run([str(script)], cwd=script.parent, check=False,
                                        capture_output=True, text=True,
                                        timeout=float(os.environ.get('ORCHESTRA_WATCH_TIMEOUT', '300')))
                output = '\n'.join((result.stdout + result.stderr).splitlines()[-40:])
                failed = result.returncode != 0 or bool(re.search(r'sem conex[aã]o|sem acesso|no connection|unreachable', output, re.I))
            except subprocess.TimeoutExpired:
                output, failed = '! Error: status command timed out / tempo esgotado', True
            old['failures'] = old['failures'] + 1 if failed else 0
            state[key] = old
            (base() / f'{key}.progress').write_text(output)
            if failed and old['failures'] < int(os.environ.get('ORCHESTRA_FAILURE_SAMPLES', '3')):
                continue
            events = [line for line in output.splitlines() if line.startswith('!')]
            old['events'] = bool(events) or old.get('events', False)
            compared = '\n'.join(events) if old['events'] and not failed else output
            if compared == old['output']:
                continue
            new_lines = set(compared.splitlines()) - set((old['output'] or '').splitlines())
            urgent = any(re.search(r'error|erro|fail|falhou|stopped|parad', line, re.I) for line in new_lines)
            if time.time() - old['sent'] < float(os.environ.get('ORCHESTRA_WATCH_INTERVAL', '3600')) and not urgent:
                continue
            matches = [agent for agent in pool if idle(agent) and Path(agent.get('cwd', '')).resolve() == script.parent.resolve()]
            if not matches:
                continue
            message = text('[WATCHER] Job state changed. Act only if needed. ', '[VIGIA] Estado dos jobs mudou. Aja somente se necessário. ')
            prompt(matches[0], message + compared[:3000], dry_run)
            if not dry_run:
                old.update(output=compared, sent=time.time())
        if not dry_run:
            save(path, state)


def local_jobs_active(cwd: Path) -> bool:
    """Checks the shared job registry before considering a session disposable."""
    configured = os.environ.get('ORCHESTRA_JOB_STATE')
    path = Path(configured or '~/.local/state/mge-localcompute/state.json').expanduser()
    if not path.exists():
        return bool(configured)
    try:
        jobs = json.loads(path.read_text())['jobs']
        for job in jobs:
            if Path('/proc', str(job['pid'])).exists() and Path(job['cwd']).resolve().is_relative_to(cwd):
                return True
    except (OSError, ValueError, KeyError, TypeError):
        return True
    return False


def idle_sessions(close: bool) -> None:
    """Reports stale sessions conservatively; closes only on explicit CLI request."""
    excluded = set(os.environ.get('ORCHESTRA_EXCLUDE', '').split(','))
    transcript_root = Path(os.environ.get('ORCHESTRA_TRANSCRIPTS', '~/.claude/projects')).expanduser()
    threshold = float(os.environ.get('ORCHESTRA_IDLE_HOURS', '12')) * 3600
    for agent in agents():
        cwd = Path(agent.get('cwd', '')).resolve()
        protected = agent.get('pane_id') in excluded or agent.get('workspace_id') in excluded
        session = (agent.get('agent_session') or {}).get('value', '')
        files = list(transcript_root.glob(f'*/{session}.jsonl')) if re.fullmatch(r'[A-Za-z0-9_-]+', session) else []
        status = cwd / 'state/current.json'
        running = True
        if status.exists():
            running = bool(json.loads(status.read_text()).get('running', True))
        candidate = (idle(agent) and cwd.is_relative_to(projects()) and not protected
                     and not (cwd / 'vigia_status.sh').exists() and not running and not local_jobs_active(cwd) and files
                     and time.time() - max(file.stat().st_mtime for file in files) > threshold)
        print(agent['pane_id'], text('IDLE candidate' if candidate else 'KEEP', 'Candidato OCIOSO' if candidate else 'MANTER'))
        if close and candidate:
            latest = next((item for item in agents() if item['pane_id'] == agent['pane_id']), {})
            if idle(latest) and not local_jobs_active(cwd) and latest.get('cwd') == agent.get('cwd') and not bool(json.loads(status.read_text()).get('running', True)) and time.time() - max(file.stat().st_mtime for file in files) > threshold:
                prompt(agent, '/exit')


def transfer_root(project: str) -> Path:
    """Validates project and handoff directory, rejecting symlinks and traversal."""
    if not re.fullmatch(r'[A-Za-z0-9_-]+', project):
        raise ValueError('Invalid project / Projeto inválido')
    folder = os.environ.get('ORCHESTRA_HANDOFF', '_handoff')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', folder):
        raise ValueError('Invalid handoff folder / Pasta de entrega inválida')
    path = projects() / project / folder
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError('Symlinks are not supported / Links simbólicos não são aceitos')
    return path


def list_handoff() -> None:
    """Lists ordinary files awaiting receipt, excluding archives and symlinks."""
    for project in sorted(projects().iterdir()):
        if not project.is_dir() or project.is_symlink() or not re.fullmatch(r'[A-Za-z0-9_-]+', project.name):
            continue
        folder = transfer_root(project.name)
        if not folder.is_dir():
            continue
        for root, dirs, files in os.walk(folder, followlinks=False):
            dirs[:] = sorted(name for name in dirs if name != '.sent' and not (Path(root) / name).is_symlink())
            for name in sorted(files):
                file = Path(root) / name
                if not file.is_symlink() and '|' not in name and '\n' not in str(file):
                    print(f'{project.name}|{file.relative_to(folder)}')


def archive_handoff(stamp: str, manifest: str) -> None:
    """Archives acknowledged files after validating the entire manifest."""
    if not re.fullmatch(r'[A-Za-z0-9_-]+', stamp):
        raise ValueError('Invalid archive label / Rótulo inválido')
    pending = []
    for line in manifest.lstrip('\ufeff').splitlines():
        if not line.strip():
            continue
        project, relative = line.split('|', 1)
        root = transfer_root(project)
        rel = Path(relative)
        if not rel.parts or rel.is_absolute() or '..' in rel.parts or '.sent' in rel.parts:
            raise ValueError('Unsafe path / Caminho inseguro')
        source = root / rel
        target = root / '.sent' / stamp / rel
        if any(path.is_symlink() for path in (source, *source.parents, target, *target.parents)) or not source.is_file() or target.exists() or any(source == item[0] for item in pending):
            raise ValueError('Missing file, duplicate or unsafe destination / Arquivo ausente, duplicado ou destino inseguro')
        pending.append((source, target))
    for source, target in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)


def main() -> int:
    """Parses each utility independently while retaining the original command names."""
    parser = argparse.ArgumentParser(description='Agent orchestration / Orquestração de agentes')
    sub = parser.add_subparsers(dest='tool', required=True)
    command = sub.add_parser('modo')
    command.add_argument('value', nargs='?')
    command = sub.add_parser('avisar')
    command.add_argument('title')
    command.add_argument('message')
    command.add_argument('priority', nargs='?', default='default')
    command = sub.add_parser('groq')
    command.add_argument('-m', '--model')
    command.add_argument('question', nargs='+')
    command = sub.add_parser('retomar_apos_limite.sh')
    command.add_argument('target')
    command.add_argument('until', nargs='?', default='never')
    command.add_argument('message', nargs='?')
    command.add_argument('--once', action='store_true')
    command.add_argument('--dry-run', action='store_true')
    command = sub.add_parser('vigia')
    command.add_argument('--dry-run', action='store_true')
    command = sub.add_parser('claudes_ociosos')
    command.add_argument('--close', '--fechar', action='store_true')
    sub.add_parser('pn-lista')
    command = sub.add_parser('pn-arquiva')
    command.add_argument('stamp')
    args = parser.parse_args()
    try:
        if args.tool == 'modo':
            mode(args.value)
        elif args.tool == 'avisar':
            notify(args.title, args.message, args.priority)
        elif args.tool == 'groq':
            groq(' '.join(args.question), args.model, '' if sys.stdin.isatty() else sys.stdin.read())
        elif args.tool == 'retomar_apos_limite.sh':
            resume(args.target, args.until, args.message, args.once, args.dry_run)
        elif args.tool == 'vigia':
            watcher(args.dry_run)
        elif args.tool == 'claudes_ociosos':
            idle_sessions(args.close)
        elif args.tool == 'pn-lista':
            list_handoff()
        else:
            with lock('handoff'):
                archive_handoff(args.stamp, sys.stdin.read())
    except urllib.error.HTTPError as error:
        print(f'HTTP error / Erro HTTP: {error.code}', file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f'Error / Erro: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
