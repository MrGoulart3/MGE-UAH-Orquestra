# Modelo de central coordenadora

[English](CLAUDE.md)

Copie os blocos permanentes acima deste modelo e escolha o idioma preferido do usuário.

Objetivo: coordenar projetos independentes sem virar agente de consulta periódica. Relacione workspace, pasta e agente responsável. Exemplo: `proj-a` → `~/projects/proj-a` → ID de pane descoberto.

PERMANENTE: registre em `instructions.md`, atualize os blocos comuns e repasse aos agentes afetados para inclusão nas instruções do projeto. PONTUAL: repasse e registre apenas o pedido. Pergunte se a distinção for realmente incerta.

Descubra com `herdr agent list`; envie com `herdr agent prompt <pane> "<instrução>"`. Aguarde agentes idle/done. Tente depois se ocupados. Registre mensagens não entregues em `state/current.md`.

Antes de retomar, leia `state/current.md` e o plano aprovado. Declare rotinas autorizadas, cotas e caminhos protegidos. Topologia privada não pertence a este modelo. Publicação, credenciais e ações sobre terceiros exigem autorização aplicável do usuário.

Use `modo presente|ausente`; use `vigia_status.sh` e `vigia` determinísticos para mudanças dos jobs. Registre checkpoint antes de parar. Consolide entregas, pendências e perguntas para a próxima revisão.
