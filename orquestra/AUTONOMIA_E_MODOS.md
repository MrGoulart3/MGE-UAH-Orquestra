# Autonomia, modos e aprovação: fonte única (mescla com o UAH-lite, 11/10/2026)

## Modo do usuário: `~/.claude/modo_mario` (ler com `modo`)

- **Quem troca:** só o diretrizes, quando o usuário disser algo como "estou disponível" / "voltei" → `presente`, ou "vou dormir / sair / ficar fora" → `ausente`. Vale qualquer jeito de dizer; o diretrizes reconhece pelo sentido.
  - O comando `modo presente|ausente` registra a troca e avisa o usuário no celular.
  - O diretrizes avisa todos os spaces.
- **PRESENTE:**
  - Em projeto de risco medium/high, nada de alterar ou executar antes do plano aprovado (`plan/approved.md`, aprovado pelo usuário: `uah.py approve`).
  - Decisões novas são perguntadas na hora.
- **AUSENTE:**
  - Executa SOMENTE o que já está aprovado (plano ou fatia aprovados) e as ações L3+ da tabela abaixo.
  - Planos novos ficam como rascunho em `plan/` esperando o usuário. Dúvidas vão para "PERGUNTAS PARA O MARIO" no CONTINUIDADE.md.
  - Pedidos de confirmação (ask) são recusados sozinhos depois de ~2 min. Nesse caso: anotar e seguir com outra coisa.
- **A decisão de seguir ou não é sempre do usuário.** O modo AUSENTE só adia a decisão, nunca a dispensa.

## Níveis de autonomia (L0–L5, do UAH)

- **L0** só sugere (o humano decide).
- **L1** executa depois do OK.
- **L2** executa e valida com um teste ou script.
- **L3** executa, valida e corrige 1 vez.
- **L4** executa, corrige e integra ao estado do projeto.
- **L5** fluxo autônomo dentro do escopo.

| Ação | Padrão | Observações |
|---|---|---|
| Ler, buscar, consultar o grafo | L4 | — |
| Criar arquivo novo na pasta do projeto | L3 | — |
| Alterar arquivo existente | L2 | L1 em `protected_paths` (manuscrito, dado bruto) |
| Apagar | L0 | — |
| Rodar ferramentas declaradas (scripts, testes, `rodar_local`, pandoc, quarto render) | L3 | — |
| Lançar cálculo em cluster dentro das cotas | L3 | L0 se `servidores.so_leitura: true` (projeto só leitura) |
| Derrubar o próprio cálculo; reiniciar o que estourou o tempo pela regra do projeto | L3 | — |
| Mexer em processo ou arquivo de outra pessoa | proibido | — |
| Instalar pacote ou ferramenta | L1 | — |
| Publicar ou enviar (Artifact público, e-mail, push para repositório que não é do projeto) | L0–L1 | — |
| Push para o repositório privado do projeto do próprio space | L3 | só depois de um commit coerente, nunca com force |
| Gastar créditos | L3 até a trava | tarefa NOVA grande (> ~200 mil tokens) = L1 |

- Cada projeto ajusta em `project.yaml → autonomia.overrides`, só para endurecer, ou para afrouxar com OK do usuário registrado.

### Ações L3 da central (exemplo)
- Ocupar recursos ociosos seguindo a prioridade definida pelo usuário; compactar sessões com contexto > 50%; repassar pedidos do usuário que só mexem em páginas/arquivos/rotinas; stand-by quando passar da trava; fila de melhorias noturnas e resumo da manhã.

## Créditos (regra central)

- **Trava:** 80% do medidor de 5 h (era 50%). Acima disso: stand-by leve, sem subagentes, até o reset.
- **À noite, sem space prioritário definido pelo usuário:** pode zerar. O vigia retoma sozinho quando os créditos voltam, então grave antes o estado no CONTINUIDADE.
- **À noite, com space prioritário:** os demais respeitam os 80%.
- **Diretrizes:** a trava vale em tarefa longa dele; atualizações rápidas e pedidos diretos do usuário não param.
- **Economia continua igual:** grátis → Codex → Claude. Subagentes Sonnet em lotes pequenos.

## Proibições globais (hook `~/.claude/hooks/guard-global/guard.py`, vale em todos os spaces)

- **DENY (nunca):**
  - `rm -r` na raiz, na home ou em `.`;
  - `curl|wget … | sh`;
  - `git push --force`;
  - `mkfs`/`dd of=/dev`;
  - `gh repo delete`;
  - `pkill -f`/`killall` (matar só por PID);
  - `ssh <cluster> … rm -r`;
  - mexer em o acesso remoto protegido;
  - `crontab -r`.
- **ASK (confirmação humana):**
  - `git push` fora dos repositórios do projeto;
  - ação pública no GitHub;
  - publicar pacote;
  - `scp`/`rsync` para máquina que não é um cluster nosso;
  - `curl` enviando dados, fora do ntfy e do groq;
  - e-mail;
  - `sudo`;
  - `git reset --hard`/`clean -f`;
  - instalar (`quarto install`, `tlmgr`, `apt`);
  - `herdr workspace/tab/pane close`.
- **Log:** `~/.claude/hooks/guard-global/guard.log`. Teste: `python3 -I ~/.claude/hooks/guard-global/guard.py --test`.

## Configuração de projeto

- Cada space tem `project.yaml`, a partir do modelo `templates/project.yaml` (compatível com o UAH-lite: `uah.py compile` lê `policy`).
- Git privado do projeto na conta do usuário: v1 = antes da mescla, v2 = depois.
