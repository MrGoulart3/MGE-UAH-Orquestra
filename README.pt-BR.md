# MGE-UAH-Orquestra

*[English version](README.md)*

**UAH-Orquestra é uma adaptação do [Universal Agent Harness (UAH)](https://github.com/fatioleg/Universal-Agent-Harness), criado pelos colaboradores do projeto original.** O original define como configurar e fiscalizar *um* projeto com agentes de IA (Claude Code, Codex): permissões, aprovação de plano e estado retomável. Esta adaptação acrescenta **orquestração de vários projetos ao mesmo tempo**, com coordenação opcional, o terminal herdr, políticas de crédito por projeto e trabalho retomável.

O código do UAH-lite em `uah-lite/` é uma cópia do original na versão 0.9.0 (commit `d26b183`) com pequenas alterações descritas abaixo. A licença MIT original foi mantida.

## O que vem do UAH original
- `project.yaml` (configuração H2), `plan/approved.md` com **aprovação humana travada por hash** (gate G1) e `state/current.md`.
- Proibições e confirmações **compiladas** em permissões e hooks do Claude Code (`uah.py compile`), com níveis de risco low, medium e high.
- Níveis de autonomia L0–L5 por tipo de ação e princípios como preservar fontes, checagens determinísticas primeiro e revisão independente.
- Catálogo de integrações: Workflow_Digestion, publish-documents, CalcBoard, sci-figures, specboard (todas do mesmo autor).

## O que esta adaptação acrescenta
| Peça | O que faz |
|---|---|
| **Coordenação opcional** | Escolha o nome do workspace e os projetos participantes. O agente registra instruções PERMANENTES ou PONTUAIS e repassa via `herdr agent prompt`. Cada projeto mantém seu UAH-lite. |
| **Modo PRESENTE / AUSENTE** (`orquestra/bin/modo`) | Registra a disponibilidade do usuário. Escopo aprovado e gates do projeto valem nos dois modos; decisões novas aguardam a próxima revisão do usuário. |
| **Autonomia padronizada** (`orquestra/AUTONOMIA_E_MODOS.md`) | Uma tabela L0–L5 única para todos os projetos, ajustável por projeto. |
| **Economia de créditos** | Configure provedores, prioridades e limites por projeto. O limite sugerido é 0,80 da janela de uso do seu provedor; esgotar o orçamento fica desativado por padrão. São instruções para os agentes, não um medidor automático. A retomada opcional (`orquestra/bin/retomar_apos_limite.sh`) tenta continuar pendências autorizadas após avisos de limite. |
| **Guarda global** (`orquestra/hooks/guard.py`) | Hook PreToolUse válido para todos os projetos, com as proibições H0 do UAH, regras de servidores compartilhados (matar só por PID, nada de `rm -r` remoto) e exceções configuráveis para rotinas já autorizadas. Teste com `python3 guard.py --test`. |
| **`project.yaml` estendido** | Campos de orquestração dentro de `notes:` (o `uah.py` só aceita extras ali): dono, máquina principal, prioridade, créditos, servidores e cotas, dados sensíveis, repositório git. |
| **Versões git por etapa** (`orquestra/bin/git_v1.sh`) | Repositório local e commit/tag `v1` sem segredos e sem arquivos grandes (que ficam listados); depois `v2`… |
| **Capacidade da máquina** (`orquestra/bin/capacidade_pc`) | Delega ao MGE-LocalCompute por `LOCALCOMPUTE_HOME`. |
| **Roteiro de montagem** (`docs/MONTAR_ARQUITETURA_CLAUDE.pt-BR.md`) | Guia em fases para um Claude montar a arquitetura do zero, pulando as fases já feitas. |

## Alterações no UAH-lite (`uah-lite/skills/uah-init/profiles/h0.json`)
- H0 mantém confirmação explícita para `git push`, `scp`/`rsync` remoto e envio HTTP. Grants restritos do projeto podem autorizar rotinas individuais; o guard global acrescenta restrições de orquestração.
- Notas específicas do projeto podem ser editadas antes da aprovação por `policy.plan_gate_paths` (padrão `[]`). Caminhos padrão de estado e planejamento continuam disponíveis; caminhos imutáveis e protegidos continuam valendo.

## Uso rápido
```bash
cp orquestra/templates/project.yaml <projeto>/      # preencha
python3 uah-lite/skills/uah-init/uah.py --root <projeto> init --risk medium --project-id <id>
python3 <projeto>/.uah/uah.py compile               # sem BLOQUEADO
# escreva <projeto>/plan/approved.md (precisa de "## Escopo" e "pronto quando"/aceite)
python3 <projeto>/.uah/uah.py approve --by <você>    # decisão humana
```
Registre o guarda global em `~/.claude/settings.json` (PreToolUse, matcher `Bash`). Rotinas externas pedem confirmação por padrão. Configure exceções somente para comandos já autorizados; veja [configuração](docs/CONFIGURATION.pt-BR.md). `ORCHESTRA_PROJECTS` seleciona pastas para descoberta e não autoriza push.

> Nota: as novas ferramentas CLI escolhem inglês ou português por `MGE_LANG`; o harness original mantém suas convenções de idioma.

## Créditos e licença
- Original: **Universal Agent Harness**, de colaboradores do projeto original, licença MIT. https://github.com/fatioleg/Universal-Agent-Harness
- Adaptação: 2026, mesma licença MIT. Veja `LICENSE`.

## Kit genérico de orquestração

Python 3.10+ e Bash; as novas ferramentas não precisam de pacotes Python. Inclua `orquestra/bin/` no `PATH` e mantenha o checkout inteiro. Clonar não instala ferramentas, altera cron, envia prompts ou notificações. O kit usa o envelope JSON `result.agents` de `herdr agent list`; confira a compatibilidade com a versão instalada antes de automatizar.

```bash
export ORCHESTRA_PROJECTS="$HOME/projects"
export ORCHESTRA_STATE="$HOME/.local/state/mge-orchestra"
export MGE_LANG=pt-BR                    # ou en
export PATH="$PWD/orquestra/bin:$PATH"
modo presente
vigia --dry-run
retomar_apos_limite.sh todos nunca --once --dry-run
claudes_ociosos                         # relatório; --fechar envia /exit
pn-lista
printf 'proj-a|docs/result.md\n' | pn-arquiva lote-a
```

| Configuração | Padrão / função |
|---|---|
| `HERDR_BIN` | `herdr`; caminho do executável, sem comando shell |
| `ORCHESTRA_PROJECTS`, `ORCHESTRA_STATE` | `~/projects`, `~/.local/state/mge-orchestra` |
| `ORCHESTRA_NIGHT_START`, `ORCHESTRA_NIGHT_END` | 21, 8; horário de silêncio configurável no fuso local; valores iguais desativam a janela |
| `NTFY_SERVER`, `NTFY_TOPIC`, `NTFY_TOKEN` | servidor `https://ntfy.sh`; tópico obrigatório para `avisar`; token opcional via ambiente |
| `GROQ_API_KEY`, `GROQ_MODEL` | ambos obrigatórios; escolha modelo disponível no provedor, sem leitura de arquivo de credenciais |
| `ORCHESTRA_IDLE_HOURS`, `ORCHESTRA_EXCLUDE` | 12; IDs de pane/workspace protegidos separados por vírgula |
| `ORCHESTRA_TRANSCRIPTS` | `~/.claude/projects`; consulta só mtime, nunca conteúdo de transcrições |
| `ORCHESTRA_HANDOFF` | `_handoff`; `pn-arquiva` move arquivos recebidos para `.sent/<lote>/` |
| `ORCHESTRA_JOB_STATE` | Registro JSON do MGE-LocalCompute; jobs locais ativos protegem as sessões do projeto. |
| `LOCALCOMPUTE_HOME` | checkout irmão usado por `capacidade_pc` |

`avisar "Título" "Mensagem" [alta]` força prioridade baixa no horário de silêncio configurado, inclusive em urgência. Credenciais vêm apenas do ambiente. `groq [-m modelo] "pergunta" < sintetico.txt` limita o contexto de stdin a 12.000 caracteres; não envie dados privados. Ferramentas não registram chaves de API nem corpos de erros HTTP.

`claudes_ociosos` só considera sessões com mtime antigo conhecido, estado ocioso confirmado, sem vigia e `state/current.json` explicitamente com `{"running": false}`. Falta de evidência mantém a sessão. Esse estado deve incluir todos os jobs locais ou remotos. `--fechar` é explícito; a ferramenta reconfirma o estado antes de `/exit`.

A retomada verifica só as últimas dez linhas não vazias da tela para avisos de limite; tenta a cada 600 segundos (`ORCHESTRA_RESUME_INTERVAL`). Depende do texto da interface e não prova que os créditos voltaram. Escolha alvo ou `todos`, prazo local `HH:MM` ou `nunca` e mensagem opcional. Use serviço ou chamada agendada única, sem instâncias sobrepostas. Detalhes: [VIGIA](docs/VIGIA.pt-BR.md). Modelos: [blocos permanentes](orquestra/templates/BLOCOS_PERMANENTES.pt-BR.md), [central](orquestra/templates/CLAUDE.pt-BR.md), [autonomia](orquestra/AUTONOMIA_E_MODOS.pt-BR.md), [skill preparar-space](orquestra/skills/preparar-space/SKILL.pt-BR.md). Harness e créditos de terceiros permanecem em `uah-lite/`.

Validação: `python3 -m unittest discover -s orquestra/tests -v`; `python3 orquestra/hooks/guard.py --test`; `python3 -m unittest discover -s uah-lite/tests -v` (a última requer dependências de desenvolvimento do original).

Nomes de comandos em português são mantidos por compatibilidade: `modo`, `avisar`, `vigia`, `capacidade_pc`, `claudes_ociosos`, `retomar_apos_limite.sh`, `pn-lista` (listar entregas), `pn-arquiva` (arquivar entregas confirmadas) e `preparar-space` (preparar workspace). A versão em inglês explica seus significados; campos do projeto e opções do guarda estão em [configuração](docs/CONFIGURATION.pt-BR.md).

## Relacionados

- [MGE-AgentPortal](https://github.com/MrGoulart3/MGE-AgentPortal): acesso autenticado aos workspaces e painel opcional de recursos.
- [MGE-LocalCompute](https://github.com/MrGoulart3/MGE-LocalCompute): admissão de recursos compartilhados, fila noturna e guarda térmica em degraus.
