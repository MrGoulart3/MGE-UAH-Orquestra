# UAH-Orquestra

**UAH-Orquestra é uma adaptação do [Universal Agent Harness (UAH)](https://github.com/fatioleg/Universal-Agent-Harness), criado pelo Prof. Valter Carvalho-Silva (repositório `fatioleg/Universal-Agent-Harness`).** O original define como configurar e fiscalizar *um* projeto com agentes de IA (Claude Code, Codex): permissões, aprovação de plano e estado retomável. Esta adaptação, mantida por Mario Envall, junta isso a uma **orquestração de vários projetos ao mesmo tempo**, com um space central, o terminal herdr, economia de créditos e trabalho contínuo.

O código do UAH-lite em `uah-lite/` é uma cópia do original na versão 0.9.0 (commit `d26b183`) com pequenas alterações descritas abaixo. A licença MIT original foi mantida.

## O que vem do UAH original
- `project.yaml` (configuração H2), `plan/approved.md` com **aprovação humana travada por hash** (gate G1) e `state/current.md`.
- Proibições e confirmações **compiladas** em permissões e hooks do Claude Code (`uah.py compile`), com níveis de risco low, medium e high.
- Níveis de autonomia L0–L5 por tipo de ação e princípios como preservar fontes, checagens determinísticas primeiro e revisão independente.
- Catálogo de integrações: Workflow_Digestion, publish-documents, CalcBoard, sci-figures, specboard (todas do mesmo autor).

## O que esta adaptação acrescenta
| Peça | O que faz |
|---|---|
| **Space central ("diretrizes")** | Um agente coordena os demais: recebe ordens do usuário, classifica como PERMANENTE ou PONTUAL, registra e repassa a todos via `herdr agent prompt`. Cada projeto continua com o seu UAH-lite. |
| **Modo PRESENTE / AUSENTE** (`orquestra/bin/modo`) | Presente: plano aprovado antes de alterar, dúvidas na hora. Ausente (noite/fora): só executa o que já foi aprovado e as ações L3+; o resto fica para a manhã. A decisão é sempre do usuário. |
| **Autonomia padronizada** (`orquestra/AUTONOMIA_E_MODOS.md`) | Uma tabela L0–L5 única para todos os projetos, ajustável por projeto. |
| **Economia de créditos** | Escada grátis (opencode/groq/OpenRouter) → Codex → Claude. Trava em 80% do medidor de 5 h. À noite, sem projeto prioritário, pode zerar, porque um vigia sem IA retoma quando os créditos voltam (`orquestra/bin/retomar_apos_limite.sh`). |
| **Guarda global** (`orquestra/hooks/guard.py`) | Hook PreToolUse válido para todos os projetos, com as proibições H0 do UAH, regras de servidores compartilhados (matar só por PID, nada de `rm -r` remoto) e exceções configuráveis para rotinas já autorizadas. Teste com `python3 guard.py --test`. |
| **`project.yaml` estendido** | Campos de orquestração dentro de `notes:` (o `uah.py` só aceita extras ali): dono, máquina principal, prioridade, créditos, servidores e cotas, dados sensíveis, repositório git. |
| **Versões git por etapa** (`orquestra/bin/git_v1.sh`) | Repositório local e commit/tag `v1` sem segredos e sem arquivos grandes (que ficam listados); depois `v2`… |
| **Capacidade da máquina** (`orquestra/bin/capacidade_pc`) | Veredito OK / APERTADO / LOTADO antes de abrir IAs auxiliares. |
| **Roteiro de montagem** (`docs/MONTAR_ARQUITETURA_CLAUDE.md`) | Guia em fases para um Claude montar a arquitetura do zero, pulando as fases já feitas. |

## Alterações no UAH-lite (`uah-lite/skills/uah-init/profiles/h0.json`)
- `git push`, `scp`/`rsync` remoto e `curl` com envio de dados deixaram de ser "ask" no H0. Passaram para o guarda global, que libera só os destinos autorizados (repositórios do próprio projeto, servidores do usuário, serviço de avisos) e pergunta nos demais.
- `plan_gate_paths` ganhou `CONTINUIDADE.md`, `PENDENTES_CALC.md`, `_para_notebook/**`, `graphify-out/**` e `REGISTRO_CORRECOES.md`, para o estado e as notas poderem ser atualizados antes da aprovação.

## Uso rápido
```bash
cp orquestra/templates/project.yaml <projeto>/      # preencha
python3 uah-lite/skills/uah-init/uah.py --root <projeto> init --risk medium --project-id <id>
python3 <projeto>/.uah/uah.py compile               # sem BLOQUEADO
# escreva <projeto>/plan/approved.md (precisa de "## Escopo" e "pronto quando"/aceite)
python3 <projeto>/.uah/uah.py approve --by <você>    # decisão humana
```
Registre o guarda global em `~/.claude/settings.json` (PreToolUse, matcher `Bash`) e configure `GUARD_HOSTS` (aliases SSH confiáveis) e `GUARD_PROJECTS_BASE` (pasta dos projetos).

## Créditos e licença
- Original: **Universal Agent Harness**, de Prof. Valter Carvalho-Silva e colaboradores, licença MIT. https://github.com/fatioleg/Universal-Agent-Harness
- Adaptação: Mario Envall (2026), mesma licença MIT. Veja `LICENSE`.
