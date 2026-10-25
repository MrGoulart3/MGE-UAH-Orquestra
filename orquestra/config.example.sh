# Trusted shell configuration: export ORCHESTRA_CONFIG=/path/to/this/file.
export ORCHESTRA_STATE="$HOME/.local/state/mge-orchestra"
export ORCHESTRA_PROJECTS="$HOME/projects"
export ORCHESTRA_OPERATOR_LABEL="Operator"
export ORCHESTRA_COORDINATOR="w1:p1"
export ORCHESTRA_EXCLUDE=""
export ORCHESTRA_PRIORITY_PANES=""
export LOCALCOMPUTE_HOME="$HOME/tools/MGE-LocalCompute"
export USAGE_CACHE="$HOME/.claude/plugins/oh-my-claudecode/.usage-cache-anthropic.json"
# Optional absolute path to an installed usage-api.js; unset means cache only.
# export USAGE_API_MODULE="$HOME/tools/usage-api.js"
export ORCHESTRA_CLUSTERS="$HOME/.config/mge-orchestra/clusters.json"
export NIGHT_PRIORITY_CONFIG="$HOME/.config/mge-orchestra/night-priority.json"
# Explicitly enable a minimal paid morning anchor call after installing the hook.
export CICLO_ENABLE_PING=0
export CICLO_MODEL=haiku
