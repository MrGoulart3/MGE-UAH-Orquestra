# Preparar workspace de projeto

[English](SKILL.md)

1. Defina raiz, objetivo, idioma e nome do workspace com o usuário. Preserve arquivos existentes. Consulte `herdr --help` e os comandos da versão instalada; selecione abas pelo nome e descubra os IDs de pane.
2. Prepare abas `claude`, `codex`, `opencode` no mesmo cwd. Use nomes únicos e inicie só os agentes necessários com `herdr agent start <nome-unico> --kind <tipo> --pane <pane>`. Retome apenas sessões com histórico. Obtenha a confiança de pasta/hook exigida pelo aplicativo.
3. Faça `CLAUDE.md` curto a partir de `orquestra/templates/BLOCOS_PERMANENTES.pt-BR.md`: objetivo, estado, delegação, central e restrições. Referencie regras privadas localmente; nunca copie credenciais ou documentos operacionais privados para projeto público.
4. Crie `state/current.md`: entregas, pendências, IDs de jobs e próximo passo. Opcionalmente mantenha `state/current.json` com `{"running": false}` para a ferramenta de sessões ociosas; atualize ao iniciar ou concluir jobs.
5. Prepare `.graphifyignore` antes da indexação opcional: ambientes, builds, segredos, logs grandes e mídia. Confira integrações e procedência; não instale ferramentas sem relação com o projeto.
6. Se usar UAH, preencha `project.yaml`, inicialize e compile pelo harness incluído. Respeite os gates e o escopo autorizado. Criar workspace não autoriza cálculos novos, publicação ou configuração global.
7. Para tarefas longas, crie `vigia_status.sh` determinístico, com eventos estáveis, timeout finito e estados terminais. Registre cotas e use MGE-LocalCompute para admissão local.
8. Cadastre na central dentro do escopo autorizado. Valide abas, cwd, instruções, checkpoint, preflight e integrações opcionais. Registre PASS/FAIL com evidências; revisão independente somente leitura pode ser usada quando apropriada.
