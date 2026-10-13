# Autonomia e modos

[English](AUTONOMIA_E_MODOS.md)

`modo` grava presente/ausente em `ORCHESTRA_STATE/mode.json`. Somente a central troca por instrução do usuário. O modo não concede permissões: ausente continua apenas plano aprovado ou rotinas explicitamente autorizadas. Decisões novas vão para `state/current.md` para a próxima revisão. Os gates de aprovação do harness continuam valendo.

| Nível | Comportamento |
|---|---|
| L0 | Sugere; humano decide |
| L1 | Executa após aprovação |
| L2 | Executa e valida |
| L3 | Executa, valida e corrige uma vez |
| L4 | Executa, corrige e atualiza o estado |
| L5 | Conclui o fluxo autorizado autonomamente |

Exemplos: leitura L4; novos arquivos L3; alterações L2; arquivos protegidos L1; exclusão L0; testes declarados L3; instalação L1; publicação L0–L1. Computação compartilhada usa cotas por projeto; processos ou arquivos de terceiros ficam fora do escopo. Não há permissão implícita para publicação rotineira.

Prefira ferramentas determinísticas para monitoramento, modelos econômicos para tarefas simples sem dados sensíveis, agentes de implementação para código e conferência independente para decisões científicas. Feche sessões secundárias ociosas; consulte MGE-LocalCompute antes de abrir outras. Registre checkpoint antes de acabar crédito ou trocar contexto. Retome só pendências aprovadas; sem pendências, fique ocioso.
