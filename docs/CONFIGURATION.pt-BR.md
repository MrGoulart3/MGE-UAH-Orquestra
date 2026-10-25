# Adaptar o kit ao seu ambiente

[English](CONFIGURATION.md)

Nomes de workspace, aliases SSH e identificadores de projeto dos exemplos são fictícios. Escolha suas pastas, pessoas ou equipes responsáveis, ferramentas instaladas e orçamentos de recursos. Coordenação, vários agentes e MGE-LocalCompute são opcionais; um projeto pode usar apenas o harness incluído. Veja as variáveis das ferramentas no [README](../README.pt-BR.md).

O campo `language` do bootstrap é configurável (`en` por padrão; por exemplo `pt-BR`). A classificação segue essa escolha; mensagens existentes do CLI original e identificadores de comandos mantêm seu idioma.

## Política do projeto

`orquestra/templates/project.yaml` preserva chaves em português por compatibilidade. Campos de `notes:` são instruções para agentes. As ferramentas opcionais de ciclo de créditos e clusters usam configuração própria; veja [Créditos](../orquestra/docs/CREDITS.md) e [Clusters](../orquestra/docs/CLUSTERS.md).

| Campo de `notes:` | Significado / padrão sugerido |
|---|---|
| `dono` | Pessoa ou equipe responsável; substitua `<responsavel>` |
| `maquina_mestre` | Host ou ambiente principal de execução; substitua `<host>` |
| `prioridade` | Prioridade do projeto: `normal` ou `alta` |
| `creditos.perfil` | Política local de custos, inicialmente `economico`; escolha a ordem de modelos/provedores |
| `creditos.trava` | Fração sugerida para pausar, `0.80`; escolha janela de uso e fonte de medição |
| `creditos.noite_pode_zerar` | Permite esgotar o orçamento sem supervisão, `false`; disponibilidade vem de `modo`, sem horário fixo |
| `servidores.usa`, `servidores.cotas` | Aliases e cotas de recursos, `[]` e `{}`; sem limites fixos de cluster, CPU ou temperatura |
| `servidores.so_leitura` | Acesso somente leitura ao servidor, `false`; permissões efetivas dependem do harness e do servidor |
| `dados_sensiveis` | Indicador de dados sensíveis, `false`; use `true` e restrinja provedores quando necessário |
| `git.remoto`, `git.versoes` | Identificador do seu repositório e rótulos de versões locais |
| `autonomia.overrides` | Ajustes do projeto aos exemplos de autonomia, `{}` |

`policy.plan_gate_paths: []` não acrescenta arquivos particulares aos caminhos padrão de pré-aprovação. Para permitir notas de trabalho locais, use `policy.plan_gate_paths: ["notes/**"]` e recompile. Isso autoriza alterações antes da aprovação do plano; use caminhos restritos. Caminhos imutáveis e protegidos continuam valendo. Projetos existentes mantêm a implementação copiada em `.uah/` até adotarem deliberadamente o runtime atualizado; recompilar não o atualiza.

## Guarda global de Bash

A instalação do hook é uma etapa explícita. Nenhum host, serviço, prefixo de repositório ou dono recebe exceção para ações externas por padrão. Proibições prevalecem sobre exceções. O guarda usa heurísticas de comando, não é uma sandbox de segurança.

| Variável de ambiente | Padrão / efeito |
|---|---|
| `GUARD_HOSTS` | Ausente: proíbe remoção recursiva remota em todos os hosts SSH. Aliases literais separados por `|` restringem essa proibição aos hosts indicados; não autorizam cópias |
| `GUARD_PROTECTED_RE` | Ausente: sem caminho protegido específico da instalação. Regex opcional proíbe comandos que mencionem seus recursos protegidos |
| `GUARD_PROJECTS_BASE` | Ausente: push pede confirmação. Definir uma raiz autoriza explicitamente `git push [-q] [-u] origin <branch> [--tags]` dentro dela; resolve links simbólicos e não inclui raízes vizinhas |
| `GUARD_ALLOW_RULES` | `{}`: sem exceções de rotina. Objeto JSON de IDs de regras ASK para listas de regex que correspondem ao comando inteiro |
| `GUARD_LOG` | `~/.claude/hooks/guard-global/guard.log`; crie a pasta pai para habilitar o log. Comandos podem conter dados privados; mantenha o log local |
| `GUARD_GLOBAL_DISABLE` | Ausente; `1` desativa o hook global |

Exemplo de rotina restrita previamente autorizada (substitua o destino fictício):

```bash
export GUARD_ALLOW_RULES='{"H0-remote-copy":["scp result[.]txt example-cluster:incoming/result[.]txt"]}'
```

Isso não autoriza outros comandos, hosts ou arquivos. Avisos HTTPS e envio de dados a modelos continuam exigindo autorização própria. Configure concessões H2/H3 separadamente se o harness também estiver habilitado; o hook global não sobrepõe suas restrições.

## Disponibilidade, ferramentas e horário de silêncio

Escolha as abas e os modelos que usa; nomes como `claude`, `codex` e `opencode` são exemplos. Vigia e retomada fornecidos atuam atualmente em agentes Claude; outros tipos precisam de adaptador. `modo` registra presente/ausente, sem agendamento. A central é um agente opcional seguindo um modelo, não um serviço de mensagens implementado no kit.

`ORCHESTRA_NIGHT_START=21` e `ORCHESTRA_NIGHT_END=8` são padrões configuráveis de notificações no fuso local, independentes da presença. Use horas inteiras de 0 a 23. Valores iguais desativam o silêncio; são aceitas janelas no mesmo dia ou atravessando meia-noite. As ferramentas opcionais de ciclo de créditos têm orçamentos diurnos e noturnos configuráveis; veja [Créditos](../orquestra/docs/CREDITS.md). Cotas de computação são configuradas localmente.

`git_v1.sh <projeto>` cria um snapshot local `v1`. O limite padrão de tamanho por arquivo é 20 MiB (`GIT_V1_MAX_SIZE=20M`, sintaxe de `find -size` do GNU). Exclui possíveis segredos, ambientes e arquivos científicos/de mídia grandes; revise a lista de exclusões para sua área. A versão em inglês explica o nome `ARQUIVOS_FORA_DO_GIT.txt`.
