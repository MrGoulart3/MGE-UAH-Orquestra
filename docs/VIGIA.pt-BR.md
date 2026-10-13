# Vigia determinístico de jobs

[English](VIGIA.md)

Crie `vigia_status.sh` executável em cada filho direto de `ORCHESTRA_PROJECTS`. O script roda localmente no cwd do projeto; deve ser confiável, curto e somente leitura. O vigia ignora links simbólicos de projeto/script, aplica timeout (padrão 300 segundos), retém as últimas 40 linhas e acorda só agentes Claude idle/done no cwd exato.

Imprima resumos estáveis. Use `!` para eventos discretos; depois que eventos aparecerem, mudanças só de progresso deixam de acionar prompts. Não imprima horário atual nem carga continuamente variável. Exemplo:

```sh
#!/bin/sh
if test -f result.status; then
    printf '! Cálculo concluído: %s\n' "$(cat result.status)"
else
    printf 'Rodando\n'
fi
```

Falhas de conexão e saídas diferentes de zero precisam persistir por `ORCHESTRA_FAILURE_SAMPLES` amostras (padrão 3). Prompt bem-sucedido aceita o novo estado; agentes ocupados e falhas de envio são tentados nas próximas rodadas. `ORCHESTRA_WATCH_INTERVAL` vale 3600 segundos; novos eventos de erro/falha/parada ignoram esse intervalo. Progresso e estados ficam só em `ORCHESTRA_STATE`. `vigia --dry-run` imprime prompts propostos sem aceitar nova referência. Cron: `*/30 * * * * /checkout/absoluto/orquestra/bin/vigia`. Declare variáveis no crontab ou em lançador privado.
