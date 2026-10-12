#!/bin/bash
# Retoma agentes Claude do herdr depois que o limite de créditos volta (sem IA).
# Uso: retomar_apos_limite.sh <agente|todos> <hora_fim HH:MM|nunca> ["<mensagem de retomada>"]
# A cada 10 min: para cada agente (ou todos os Claude), se está parado (idle/done) e as últimas linhas da tela
# mostram o aviso de limite do Claude, manda a mensagem de retomada. Se o limite ainda não voltou, o Claude
# só repete o aviso (sem custo). Log: ~/.calc_local/retomar_<agente>.log
AG="$1"; FIM="${2:-nunca}"
MSG="${3:-RETOMADA AUTOMATICA (o limite de creditos do Claude voltou): leia o seu CONTINUIDADE.md e continue as tarefas pendentes de onde parou, com autonomia e economia de creditos. Se nao houver nada pendente, fique em stand-by e nao faca nada.}"
LOG="$HOME/.calc_local/retomar_${AG}.log"; mkdir -p "$(dirname "$LOG")"
if [ "$FIM" = nunca ]; then fim=9999999999; else
  fim=$(date -d "$FIM" +%s); [ "$fim" -le "$(date +%s)" ] && fim=$(date -d "tomorrow $FIM" +%s); fi
echo "$(date '+%F %T') inicio agente=$AG fim=$FIM" >> "$LOG"
declare -A avisado
while [ "$(date +%s)" -lt "$fim" ]; do
  lista=$(herdr agent list 2>/dev/null | python3 -I -c "import json,sys
for a in json.load(sys.stdin)['result']['agents']:
    n=a.get('name') or a['pane_id']
    if ('$AG'=='todos' and a['agent']=='claude') or '$AG' in (a.get('name'),a['pane_id']):
        print(a['pane_id'], a['agent_status'], a['cwd'].rstrip('/').split('/')[-1].replace(' ','_'))")
  while read -r pane st proj; do
    [ -n "$pane" ] || continue
    [[ "$st" == idle || "$st" == done ]] || continue
    if herdr agent read "$pane" 2>/dev/null | grep -v '^\s*$' | tail -10 | grep -qiE "hit your (usage )?limit|limit reached|usage limit|resets [0-9]{1,2}(:[0-9]{2})? ?(am|pm)"; then
      echo "$(date '+%F %T') $pane ($proj): limite na tela, status=$st -> retomada" >> "$LOG"
      herdr agent prompt "$pane" "$MSG" >> "$LOG" 2>&1
      if [ -z "${avisado[$pane]}" ]; then
        ~/bin/avisar "Limite de creditos: $proj" "Space $proj parou no limite; sera retomado sozinho quando os creditos voltarem." >/dev/null 2>&1
        avisado[$pane]=1; fi
    fi
  done <<< "$lista"
  sleep 600
done
echo "$(date '+%F %T') fim" >> "$LOG"
