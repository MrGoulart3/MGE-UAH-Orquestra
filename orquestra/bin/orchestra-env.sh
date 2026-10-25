# Shared configuration; source only a trusted operator-owned file.
ORCHESTRA_BIN=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
export ORCHESTRA_BIN
ORCHESTRA_STATE=${ORCHESTRA_STATE:-$HOME/.local/state/mge-orchestra}
export ORCHESTRA_STATE
mkdir -p "$ORCHESTRA_STATE"
[ -z "${ORCHESTRA_CONFIG:-}" ] || . "$ORCHESTRA_CONFIG"
export USAGE_CACHE=${USAGE_CACHE:-$HOME/.claude/plugins/oh-my-claudecode/.usage-cache-anthropic.json}
export ORCHESTRA_PROJECTS=${ORCHESTRA_PROJECTS:-$HOME/projects}
export PATH="$ORCHESTRA_BIN:$HOME/.local/bin:$PATH"
export ORCHESTRA_COORDINATOR=${ORCHESTRA_COORDINATOR:-}
export ORCHESTRA_DOCS=${ORCHESTRA_DOCS:-$ORCHESTRA_BIN/../docs}
herdr() { command "${HERDR_BIN:-herdr}" "$@"; }
