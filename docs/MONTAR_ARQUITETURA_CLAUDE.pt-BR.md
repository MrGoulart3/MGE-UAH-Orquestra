# Montar um workspace de projetos com vários agentes

[English](MONTAR_ARQUITETURA_CLAUDE.md)

Este guia usa o kit genérico e o harness original. Cada integração opcional é uma decisão separada de instalação; clonar o repositório não altera configurações globais.

1. **Inventário.** Confira sistema, shell, RAM, núcleos e ferramentas instaladas. Preserve workspaces e instruções existentes. Defina raízes, idioma e escopo autorizado.
2. **Terminal e agentes.** Instale herdr e os CLIs necessários pelas instruções oficiais. Confira help e envelope JSON da versão instalada. Um workspace por repo, abas nomeadas, agentes com nomes distintos e cwd comum. Abra sessões secundárias só quando precisar. Retome somente histórico existente.
3. **Central.** Use [o modelo](../orquestra/templates/CLAUDE.pt-BR.md) e [os blocos permanentes](../orquestra/templates/BLOCOS_PERMANENTES.pt-BR.md). Mantenha mapa de projetos/agentes. Diferencie PERMANENTE de PONTUAL, tente depois quando agentes estiverem ocupados e registre evidências de entrega.
4. **Harness.** Use [preparar-space](../orquestra/skills/preparar-space/SKILL.pt-BR.md). Preencha `project.yaml`, inicialize e compile UAH. Preserve gates de aprovação. Declare objetivo, dados protegidos, cotas e próxima ação.
5. **Continuidade e recursos.** Mantenha `state/current.md`; opcionalmente registre jobs em `state/current.json`. `modo` grava presença sem conceder permissões. Configure MGE-LocalCompute para PCs compartilhados; centralize os limites nele, sem fixar hardware nas instruções do projeto.
6. **Monitoramento.** Crie eventos estáveis em `vigia_status.sh`. Leia [VIGIA](VIGIA.pt-BR.md), teste com `--dry-run` e agende dentro do escopo autorizado. Confira `retomar_apos_limite.sh ... --once --dry-run` antes de habilitar prompts; a detecção depende do texto exibido pelo agente.
7. **Economia.** Resumos simples sem dados sensíveis podem usar chamadas curtas a modelos; conclusões científicas precisam de evidência independente. Chave e modelo Groq vêm do ambiente. Prefira comandos pontuais a sessões ociosas.
8. **Integrações.** Verifique fonte, licença e necessidade antes de OMC, grafos, ferramentas de documentos ou vaults. Prepare exclusões antes de indexar arquivos grandes ou dados privados. Não republique skills de terceiros sem conferir a licença.
9. **Entrega e acesso remoto.** `_handoff/` e manifestos confirmados separam entregas pendentes de arquivos `.sent/`. Configure avisos pelo ambiente; à noite a prioridade é sempre baixa. Acesso remoto, firewall e exposição do portal exigem configuração autorizada própria; consulte a segurança do projeto irmão.
10. **Validação.** Confira workspaces, abas, cwd, instruções, checkpoints, compilação, cotas e testes offline. Registre evidências, pendências e próximos passos antes de declarar a instalação pronta. Use revisão independente quando o risco justificar.
