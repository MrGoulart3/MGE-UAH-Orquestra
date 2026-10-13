#!/usr/bin/env bash
# Cria o repositório git LOCAL de um space e faz o commit "v1" (tag v1), sem enviar nada para a internet.
# Uso: git_v1.sh "<pasta do space>"
# Versiona texto, scripts, inputs, resultados e documentos pequenos (< 20 MB cada). Arquivos grandes ou binários
# pesados (.chk, .rwf, vídeo, venv, zip...) ficam FORA e são listados em ARQUIVOS_FORA_DO_GIT.txt.
# Segredos (.dat, .env, chaves, tópico ntfy) nunca entram.
set -euo pipefail
D="$1"; cd "$D"
LIM=20M
if [ ! -d .git ]; then git init -q -b main; fi
# identidade: use a sua (git config user.name / user.email)
git config core.quotepath false
cat > .gitignore.v1 <<'EOF'
# --- gerado por git_v1.sh: segredos ---
*.dat
.env
.env.*
*.pem
*.key
id_*
*ntfy_topic*
# --- ambientes, caches, build ---
venv*/
.venv/
.vevn/
node_modules/
__pycache__/
.pytest_cache/
.mypy_cache/
.ipynb_checkpoints/
build/
dist/
.omc/state/
.omc/logs/
graphify-out/cache/
*.zip
*.tar
*.tar.gz
*.tgz
*.7z
# --- binários de química pesados ---
*.chk
*.fchk
*.rwf
*.int
*.d2e
*.skr
*.cube
*.gbw
*.densities
*.tmp
*.bas*
*.wfn
*.wfx
# --- mídia pesada / render ---
*.mp4
*.mkv
*.mov
*.avi
*.blend1
*.exr
EOF
# junta com .gitignore existente (sem duplicar)
if [ -f .gitignore ]; then cat .gitignore .gitignore.v1 | awk '!s[$0]++' > .gitignore.new; mv .gitignore.new .gitignore; else mv .gitignore.v1 .gitignore; fi
rm -f .gitignore.v1
# arquivos grandes: listar e ignorar
find . -path ./.git -prune -o -type f -size +$LIM -print | sed 's#^\./##' | sort > ARQUIVOS_FORA_DO_GIT.txt
if [ -s ARQUIVOS_FORA_DO_GIT.txt ]; then
  { echo "# --- arquivos > $LIM (lista em ARQUIVOS_FORA_DO_GIT.txt) ---"; sed 's#^#/#; s#\([][*?]\)#\\\1#g' ARQUIVOS_FORA_DO_GIT.txt; } >> .gitignore
fi
git add -A
git commit -q -m "v1: estado do space antes da mescla com o UAH" || true
git tag -f v1 >/dev/null
echo "$(basename "$D"): $(git ls-files | wc -l) arquivos versionados; $(du -sh .git | cut -f1) em .git; fora (grandes): $(wc -l < ARQUIVOS_FORA_DO_GIT.txt)"
