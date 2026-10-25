# Diretrizes permanentes compartilhadas

[English](BLOCOS_PERMANENTES.md)

> Workspace `<nome-projeto>` usa abas nomeadas `claude`, `codex`, `opencode`; descubra os IDs de pane, sem depender da ordem das abas.
> Leia `CONTINUIDADE.md` (sincronize `state/current.md` quando exigido pelo harness) antes de retomar; registre entregas, identificadores de jobs em execução, perguntas pendentes e próxima ação antes de parar.
> Prefira scripts determinísticos de status. Delegue somente tarefas simples sem dados sensíveis a modelos econômicos; confira números independentemente.
> Compartilhe o orçamento de recursos pelo MGE-LocalCompute. Nunca contorne as travas nem altere processos de terceiros.
> Mantenha sessões interativas secundárias fechadas quando ociosas. Prefira comandos pontuais.
> A central distingue diretrizes PERMANENTES de pedidos PONTUAIS, mantém esta fonte e repassa alterações sem interromper agentes ocupados.
> Preserve dados originais. Nunca inclua segredos, endereços privados ou resultados inéditos em repositórios públicos, pedidos a modelos ou notificações.
> Use `_handoff/` para entregas com recebimento confirmado. Avisos usam ntfy configurado e ficam silenciosos na janela noturna configurada.
> Presença não altera autorização. Ausente continua trabalho aprovado e registra decisões novas para revisão.
> Se uma ambiguidade real mudar o resultado, pergunte antes do trabalho dependente.

> **Atualização 2026-10-24:** recados comuns usam `enviar_space` e aguardam o fim da tarefa; `URGENTE=1` só para proteção e sessão. Créditos: dia 75/80, noite 90/95, teto matutino padrão 30%; a porta é aplicada pelo hook, com exceções temporárias explícitas. Cálculo pronto pede `pedir_vaga`; após lançar, registra `registrar_job`, sem responder ao coordenador. Reinício barato salva handoff; cancelamento persiste até liberação. Entregas usam `deliver_file`, links usam `central_add`. Cálculos leves sempre passam por LocalCompute, com registro único e guarda de RAM. Configuração e detalhes: `docs/` por sistema; nenhuma prioridade ou máquina de pesquisa é predefinida.
