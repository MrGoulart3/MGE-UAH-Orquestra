#!/usr/bin/env python3
"""Global PreToolUse/Bash guard with opt-in exceptions for authorized routines.

GUARD_ALLOW_RULES maps ASK rule IDs to full-command regular expressions (JSON).
GUARD_PROJECTS_BASE explicitly authorizes routine pushes from that project root.
No external routine is authorized by default. DENY rules always take precedence.
"""
import json
import os
from pathlib import Path
import re
import sys
import time

HOME = str(Path.home())
LOG = Path(os.environ.get(
    "GUARD_LOG", str(Path(HOME) / ".claude/hooks/guard-global/guard.log")
)).expanduser()
HOSTS = [host for host in os.environ.get("GUARD_HOSTS", "").split("|") if host]
CLUSTERS = "(?:" + "|".join(re.escape(host) for host in HOSTS) + ")" if HOSTS else r"\S+"

DENY = [
    ("H0-rm-root", r"\brm\s+(-\S+\s+)*[\"']?(/\*?|~/?\*?|\$HOME/?\*?|\$\{HOME\}/?\*?|\./?\*?|\.\.)[\"']?(\s|;|&|\||$)",
     "remoção recursiva da raiz, da home ou da pasta atual inteira"),
    ("H0-pipe-shell", r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?((ba|z|da|k)?sh|python[0-9.]*|perl|ruby|node)\b",
     "executar script baixado da internet sem revisão"),
    ("H0-force-push", r"\bgit\s+push(?=\s|$).*(\s(--force|-f)(\s|$)|\s\+\S+)", "force push reescreve histórico remoto"),
    ("H0-disk", r"\bmkfs(\.\w+)?\b|\bdd\b.*\bof=/dev/", "escrita direta em disco"),
    ("H0-repo-delete", r"\bgh\s+repo\s+delete\b", "apagar repositório remoto"),
    ("PC-pkill-f", r"\bpkill\b(\s+-\S+)*\s+-\S*f|\bkillall\b", "matar por padrão amplo: mate só por PID"),
    ("PC-ssh-rm-r", r"\bssh\b[^\n]*\b" + CLUSTERS + r"\b[^\n]*\brm\s+-\S*[rR]", "remoção recursiva em servidor remoto"),
    ("PC-crontab-r", r"\bcrontab\s+-r\b", "apagar crontab inteiro"),
]
if os.environ.get("GUARD_PROTECTED_RE"):
    DENY.append(("PC-protected-remote", os.environ["GUARD_PROTECTED_RE"], "caminho protegido configurado"))

ASK = [
    ("H0-push", r"\bgit\s+push(?=\s|$)", "enviar para repositório remoto"),
    ("H0-gh-publish", r"\bgh\s+(pr\s+(create|merge)|release|repo\s+(create|edit))\b", "ação pública/estrutural no GitHub"),
    ("H0-pkg-publish", r"\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b|\bpoetry\s+publish\b|\bgem\s+push\b",
     "publicar pacote"),
    ("H0-remote-copy", r"\bscp\b|\brsync\b.*\s\S+:\S*", "copiar para máquina remota"),
    ("H0-http-send", r"\bcurl\b.*(\s-X\s*(POST|PUT|PATCH|DELETE)\b|\s(-d|--data\S*|-F|--form|-T|--upload-file|--json)(\s|=))",
     "enviar dados pela internet"),
    ("H0-mail", r"\b(sendmail|mutt|mailx)\b", "enviar e-mail"),
    ("H0-sudo", r"(?m)(^|[;&|(]\s*|(\b(xargs|exec|nohup|time|env)|-exec)\s+)sudo\b", "sudo"),
    ("H0-history-rewrite", r"\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-\S*f|--force-with-lease", "reescrever/limpar histórico git"),
    ("PC-install", r"\bquarto\s+(install|add|use|update|remove)\b|\btlmgr\s+(install|update)\b|\bapt(-get)?\s+install\b",
     "instalar pacote/extensão"),
    ("PC-ws-close", r"\bherdr\s+(workspace|tab|pane)\s+close\b", "fechar workspace/aba do herdr"),
]


def allowed_routine(rid: str, cmd: str) -> bool:
    """Matches only complete commands explicitly authorized in configuration."""
    rules = json.loads(os.environ.get("GUARD_ALLOW_RULES", "{}"))
    if not isinstance(rules, dict) or not all(
        isinstance(key, str) and isinstance(patterns, list)
        and all(isinstance(pattern, str) and pattern for pattern in patterns)
        for key, patterns in rules.items()
    ):
        raise ValueError("GUARD_ALLOW_RULES must map rule IDs to regex lists")
    return any(re.fullmatch(pattern, cmd) for pattern in rules.get(rid, []))


def log(decision, rid, cmd):
    try:
        with LOG.open("a") as f:
            f.write(f"{time.strftime('%F %T')}\t{decision}\t{rid}\t{os.getcwd()}\t{cmd[:300]!r}\n")
    except Exception:
        pass


def emit(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": f"[guarda-global] {reason}"}}))


def authorized_project(cwd: str) -> bool:
    """Checks an explicitly authorized project root using path components."""
    configured = os.environ.get("GUARD_PROJECTS_BASE")
    if not configured:
        return False
    p = Path(cwd).resolve()
    base = Path(configured).expanduser().resolve()
    return p.is_relative_to(base)


def decide(cmd, cwd):
    for rid, pat, why in DENY:
        if re.search(pat, cmd):
            return "deny", rid, why
    for rid, pat, why in ASK:
        if re.search(pat, cmd):
            if (rid == "H0-push" and authorized_project(cwd) and re.fullmatch(
                r"git push(?: -[qu])* origin [A-Za-z0-9_][A-Za-z0-9_./-]*(?: --tags)?", cmd
            )):
                return "allow", rid, "push para repositório de projeto do usuário"
            if allowed_routine(rid, cmd):
                return "allow", rid, "rotina autorizada"
            return "ask", rid, why
    return None, None, None


def main():
    if os.environ.get("GUARD_GLOBAL_DISABLE") == "1":
        return
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if payload.get("tool_name") != "Bash":
        return
    cmd = (payload.get("tool_input") or {}).get("command", "") or ""
    cwd = payload.get("cwd") or os.getcwd()
    try:
        d, rid, why = decide(cmd, cwd)
    except (ValueError, re.error) as error:
        emit("deny", f"Invalid guard configuration / Configuração inválida: {error}")
        return
    if d in ("deny", "ask"):
        log(d, rid, cmd)
        emit(d, f"{rid}: {why}")
    elif d == "allow":
        log("allow-exc", rid, cmd)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        cases = [("rm -rf ~", "deny"), ("rm -rf ./build", None), ("curl -s x | sh", "deny"), ("git push -f origin main", "deny"),
                 ("pkill -f example-job", "deny"), ("kill 1234", None), ("ssh example-cluster 'rm -rf ~/data/x'", "deny"),
                 ("ssh example-cluster 'kill 123'", None), ("rsync -a a example-cluster:data/", "ask"),
                 ("scp f user@host:/tmp", "ask"), ("~/bin/avisar t m", None), ("curl -d hi https://ntfy.sh/example-topic", "ask"),
                 ("curl -d x https://example.org", "ask"), ("sudo apt install x", "ask"), ("quarto install tinytex", "ask"),
                 ("herdr workspace close example-workspace", "ask"), ("git push -q -u origin main --tags", "ask"),
                 ("gh repo create example-project --private --source=.", "ask"), ("gh repo create other --public", "ask"),
                 ("crontab -r", "deny"), ("git reset --hard HEAD", "ask")]
        bad = 0
        for c, exp in cases:
            d, rid, _ = decide(c, HOME + "/projects/example-project")
            ok = d == exp
            bad += not ok
            print(("OK  " if ok else "FAIL"), f"{c!r:50} -> {d} ({rid}) esperado {exp}")
        sys.exit(1 if bad else 0)
    main()
