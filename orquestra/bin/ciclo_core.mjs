import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync, spawn} from 'node:child_process';
const morningCap=Number(process.env.CYCLE_MORNING_CAP || 30);
if (!(morningCap>0&&morningCap<=100)) throw Error('Invalid CYCLE_MORNING_CAP');
const home=process.env.HOME, o=process.env.ORCHESTRA_STATE, bin=process.env.ORCHESTRA_BIN;
fs.mkdirSync(o,{recursive:true});
const file=n=>`${o}/${n}`;
const read=(n,d='')=>{try{return fs.readFileSync(file(n),'utf8').trim();}catch{return d;}};
const put=(n,v)=>{fs.writeFileSync(file(`${n}.tmp`),String(v)+'\n');fs.renameSync(file(`${n}.tmp`),file(n));};
const del=n=>fs.rmSync(file(n),{force:true});
const now=()=>Number(process.env.AGORA ?? Date.now()/1000);
const run=(cmd,args=[],env={})=>spawnSync(cmd,args,{encoding:'utf8',timeout:180000,env:{...process.env,...env}});
const log=m=>{const s=`${new Date(now()*1000).toISOString()} ${m}`;fs.appendFileSync(file('ciclo.log'),s+'\n');console.log(s);};
const alert=m=>{log(m);const r=run(`${bin}/avisar`,['Ciclo matutino',m]);if(r.status!==0)log('Falha ao enviar aviso ao celular');};
const conf=()=>read('ciclo.conf','ANCORA=05:00').match(/^ANCORA=(\d\d:\d\d)$/m)?.[1] || '05:00';
const tol=()=>{const v=Number(read('ciclo.conf').match(/^TOL=(\d+)$/m)?.[1]??30);if(v<0||v>=150)throw Error('TOL deve estar entre 0 e 149 minutos');return v*60;};
const hh=t=>new Date(t*1000).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
function anchors(t){const [h,m]=conf().split(':').map(Number);let d=new Date(t*1000);d.setHours(h,m,0,0);const today=d.getTime()/1000; if(today<=t)d.setDate(d.getDate()+1);return {today,next:d.getTime()/1000};}
function meter(so=false){const r=run(`${bin}/medidor`,[],so?{MEDIDOR_SO_CACHE:'1'}:{});if(r.status!==0)throw Error('medidor indisponível');const [p,s,age]=r.stdout.trim().split(/\s+/);const reset=s==='-'?null:Date.parse(s)/1000;if(!Number.isFinite(Number(p)) || Number(p)<0 || !Number.isFinite(Number(age)) || Number(age)>1200 || (s!=='-'&&!Number.isFinite(reset)))throw Error('resposta inválida/antiga do medidor');return {pct:Number(p),reset};}
function expire(t){if(fs.existsSync(file('CICLO_LIBERADO'))){const expiry=Number(read('CICLO_LIBERADO'));if(!Number.isFinite(expiry)||expiry<=t)del('CICLO_LIBERADO');}}
function once(key,fn){if(read(key)!=='1'){fn();put(key,'1');}}
function excecoes(){return read('porta_excecoes').split('\n').map(l=>{const i=l.lastIndexOf('|');return [l.slice(0,i),Number(l.slice(i+1))];}).filter(([p,v])=>p&&v>now());}
function escapeWorking(){const r=run('herdr',['agent','list']);if(r.status!==0){log('Falha ao listar agentes para Escape');return;}const exc=excecoes();try{for(const a of JSON.parse(r.stdout).result.agents){if(a.agent==='claude'&&a.agent_status==='working'&&!exc.some(([p])=>a.cwd===p||(a.cwd||'').startsWith(p+'/'))){const e=run('herdr',['agent','send-keys',a.pane_id,'Escape']);if(e.status!==0)log(`Escape falhou: ${a.pane_id}`);}}}catch{log('Lista de agentes inválida');}}
function close(){put('PORTA_FECHADA',conf());log('porta fechada');escapeWorking();}
function daily(){let errors=0;const check=(name,ok)=>{log(`${ok?'OK':'FALHA'} ${name}`);if(!ok)errors++;};
 let executable=false;try{fs.accessSync(`${home}/.local/bin/claude`,fs.constants.X_OK);executable=true;}catch{}
 check('caminho do claude',executable);
 let installed=false;try{const hooks=JSON.parse(fs.readFileSync(`${home}/.claude/settings.json`)).hooks?.UserPromptSubmit;installed=hooks?.some(g=>g.hooks?.some(h=>h.type==='command'&&/(?:^|[ /])ciclo_porta_hook(?:\s|$)/.test(h.command)));}catch{}
 check('hook instalado',installed);
 const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'ciclo-hook-'));
 try{fs.mkdirSync(`${tmp}/.orquestra`);fs.writeFileSync(`${tmp}/.orquestra/PORTA_FECHADA`,'');fs.writeFileSync(`${tmp}/.orquestra/ciclo.conf`,`ANCORA=${conf()}`);
 fs.writeFileSync(`${tmp}/input.json`,'{"prompt":"teste"}');
 const probe=env=>{const fd=fs.openSync(`${tmp}/input.json`,'r');try{return spawnSync(`${bin}/ciclo_porta_hook`,[],{stdio:[fd,'pipe','pipe'],encoding:'utf8',timeout:5000,env:{...process.env,HOME:tmp,ORCHESTRA_STATE:`${tmp}/.orquestra`,CICLO_ANCORA:'',...env}});}finally{fs.closeSync(fd);}};
 let b=probe({}), a=probe({CICLO_ANCORA:'1'});fs.writeFileSync(`${tmp}/.orquestra/CICLO_LIBERADO`,'');let l=probe({});fs.rmSync(`${tmp}/.orquestra/CICLO_LIBERADO`);fs.rmSync(`${tmp}/.orquestra/PORTA_FECHADA`);let f=probe({});
 check('hook bloqueia/libera simulado',b.status===0&&JSON.parse(b.stdout).decision==='block'&&[a,l,f].every(r=>r.status===0&&!r.stdout));
 }catch{check('hook bloqueia/libera simulado',false);}finally{fs.rmSync(tmp,{recursive:true,force:true});}
 try{meter();check('medidor responde',true);}catch{check('medidor responde',false);}
 const cron=run('crontab',['-l']).stdout||'';
 const lines=cron.split('\n').filter(l=>l.trim()&&!l.trim().startsWith('#'));
 check('cron controle a cada 5 min',lines.some(l=>/^\*\/5\s+\*\s+\*\s+\*\s+\*\s+.*(?:\/|\s)ciclo_controle(?:\s|$)/.test(l)&&!l.includes('--teste')));
 check('cron teste diário 21:00',lines.some(l=>/^0\s+21\s+\*\s+\*\s+\*\s+.*ciclo_controle\s+--teste(?:\s|$)/.test(l)));
 // 20/10: reservas independentes da âncora (cron + timer systemd) e o acordar dos spaces
 check('cron reserva da âncora',lines.some(l=>/^\S+\s+\*\s+\*\s+\*\s+\*\s+.*ancora_reserva(?:\s|$)/.test(l)));
 const ex=n=>{try{fs.accessSync(`${bin}/${n}`,fs.constants.X_OK);return true;}catch{return false;}};
 check('ancora_reserva e acordar_manha executáveis',ex('ancora_reserva')&&ex('acordar_manha'));
 const timer=process.env.CICLO_TIMER_FAKE??run('systemctl',['--user','is-active','ciclo-reserva.timer'],{XDG_RUNTIME_DIR:`/run/user/${process.getuid()}`,DBUS_SESSION_BUS_ADDRESS:`unix:path=/run/user/${process.getuid()}/bus`}).stdout.trim();
 check('timer systemd da reserva ativo',timer==='active');
 console.log(`Âncora: ${conf()}`);if(errors)alert(`Teste diário: ${errors} falha(s); consulte ciclo.log/saída do teste`);return errors?1:0;
}
function schedule(t){const {today,next}=anchors(t);const a=t<=today+tol()+600?today:next;return {a,early:a-tol(),late:a+tol(),cut:a-18000+tol()};}
function plan(){const t=now(),{a,early,late,cut}=schedule(t),m=meter();let r=m.reset??t;while(r<=cut)r+=18000;const end=r,begin=end-18000,morning=end>=early&&end<=late?end:early;const msg=`Plano: última janela ${hh(begin)}–${hh(end)}; pausa ${Math.round(Math.max(0,(morning-end)/60))} min; manhã ${hh(morning)}; renovação ${hh(morning+18000)}; corte ${hh(cut)}`;fs.appendFileSync(file('ciclo_plano.log'),new Date(t*1000).toISOString()+' '+msg+'\n');console.log(msg);}
function spaces(msg){const r=run('herdr',['agent','list']);if(r.status!==0)return;try{for(const x of JSON.parse(r.stdout).result.agents){if(x.agent==='claude'&&!(process.env.ORCHESTRA_EXCLUDE||'').split(',').includes(x.workspace_id))spawn(`${bin}/enviar_space`,[x.pane_id,msg,'60'],{detached:true,stdio:'ignore',env:{...process.env,NAO_GUARDAR:'1',URGENTE:'1'}}).unref();}}catch{log('Lista de agentes inválida');}}
function wake(){const r=spawn(`${bin}/acordar_manha`,[],{detached:true,stdio:'ignore'});r.on('error',()=>log('acordar_manha indisponível'));r.unref();log('acordar_manha chamado');}
async function control(){const t=now();expire(t);const {a,early,late,cut}=schedule(t);
 let pending=Number(read('ciclo.pendente','0'));
 if(pending&&t>pending+3600){del('ciclo.pendente');pending=0;}
 const liberado=fs.existsSync(file('CICLO_LIBERADO'));
 // operator 20/10: teto RÍGIDO de 30% em toda a janela da manhã, até segunda ordem (porta fechada até ela renovar).
 const teto=Number(read('ciclo.teto','0'));
 if(teto&&t<teto&&!liberado){put('PORTA_FECHADA',`${hh(teto)} (teto de ${morningCap}% da manhã)`);log('teto da manhã; porta fechada até '+hh(teto));escapeWorking();return;}
 if(teto){del('ciclo.teto');del('PORTA_FECHADA');}
 const manha=Number(read('ciclo.manha','0')),naManha=manha&&t>=manha&&t<manha+18000,noite=t>=cut-18000&&t<early;
 const fechada=fs.existsSync(file('PORTA_FECHADA'))&&t>=cut&&t<early;let m0=null;
 if((naManha||noite)&&!liberado&&read('ciclo.parado')!==String(a)){let m=null;try{m=meter(fechada);}catch{}m0=m;
   if(m&&naManha&&m.pct>=morningCap){const fim=m.reset&&m.reset>t?m.reset:manha+18000;put('ciclo.teto',fim);put('PORTA_FECHADA',`${hh(fim)} (teto de ${morningCap}% da manhã)`);log(`teto da manhã: ${m.pct}%; porta fechada até ${hh(fim)}`);escapeWorking();return;}
   // operator 20/10: na última janela da noite (termina entre o corte e a manhã), em ~80% ninguém faz nada até a âncora.
   const ultima=m&&!naManha&&m.reset&&m.reset>t&&m.reset>cut&&m.reset<=late;
   // 22/10 (operator): limite da última janela ajustável por noite: "$ORCHESTRA_STATE"/ciclo.limite_noite = 'PCT|até_epoch' (vencido → 80)
   const [lv,lu]=String(read('ciclo.limite_noite','')).split('|'),LIM=(Number(lu)>t&&Number(lv)>0)?Number(lv):80;
   if(ultima&&m.pct>=LIM-5&&m.pct<LIM)once(`ciclo.aviso75-${a}`,()=>{spaces(`CICLO (automático, sem IA): créditos em ${m.pct}%. Em ${LIM}% a porta do ciclo fecha até ${hh(early)} (operator). Grave o CONTINUIDADE agora e termine só o passo atual.`);log(`aviso 75%: porta fecha em 80% até ${hh(early)}`);});
   if(ultima&&m.pct>=LIM){put('ciclo.parado',a);close();put('ECONOMIA_ATE',early);log(`${LIM}% na última janela da noite (${m.pct}%): porta fechada até ${hh(early)}`);return;}
 }
 if(read('ciclo.parado')===String(a)&&t<early&&!liberado){put('PORTA_FECHADA',hh(early));escapeWorking();return;}
 if(read('ciclo.dia')===String(a)){del('PORTA_FECHADA');return;}
 // revisão: com TOL < 5 min, uma janela aberta entre o corte e o 1º cron depois dele perderia a noite
 if(t<cut&&t>=cut-300&&!liberado&&m0&&(!m0.reset||m0.reset<=t)){close();log('sem janela ativa perto do corte; porta fechada');return;}
 if(t<cut){del('PORTA_FECHADA');log('antes do corte; porta aberta');return;}
 if(fs.existsSync(file('CICLO_LIBERADO'))){del('PORTA_FECHADA');log('ciclo liberado até a âncora');return;}
 // 20/10: medidor fora não impede o ping da manhã (antes ficava porta fechada e sem âncora).
 let m;try{m=meter(fechada);}catch(e){if(!fechada)once(`ciclo.erro-${a}`,()=>alert(e.message));if(t<early&&!pending){close();return;}m={pct:0,reset:null};}
 if(!pending){
   // revisão: janela que começou depois do corte NÃO abre a porta (operator: silêncio até a âncora)
   if(m.reset&&m.reset>late&&t<early){put('PORTA_FECHADA',hh(early));escapeWorking();once(`ciclo.perdido-${a}`,()=>alert('Janela começou depois do corte; porta segue fechada até '+hh(early)));return;}
   if(t>late+300){del('PORTA_FECHADA');return;}
   pending=m.reset&&m.reset>=early&&m.reset<=late?m.reset:early;put('ciclo.pendente',pending);
 }
 if(t>=pending){
   put('ciclo.dia',a);del('CICLO_LIBERADO');let success=false;
   for(const [i,offset] of [0,120,300].entries()){
     const wait=Math.max(0,pending+offset-now());
     if(wait){if(process.env.AGORA!==undefined)process.env.AGORA=String(now()+wait);else await new Promise(resolve=>setTimeout(resolve,wait*1000));}
     const r=run(`${bin}/ancorar_janela`,[],{CICLO_ANCORA:'1'});log(`âncora tentativa ${i+1} rc=${r.status}`);
     try{const n=meter();if(r.status===0&&n.reset&&Math.abs(n.reset-(now()+18000))<=600){success=true;put('ciclo.manha',n.reset-18000);break;}}
     catch(e){log(e.message);if(r.status===0){success=true;put('ciclo.manha',now());log('ping rc=0; medidor fora, janela não conferida');break;}}
   }
   del('PORTA_FECHADA');del('ciclo.pendente');del('ciclo.parado');log(success?'âncora confirmada; porta aberta':'âncora falhou após 3 tentativas; porta aberta');
   wake();
   log('Resumo da manhã: '+read('ciclo_plano.log','sem plano registrado').split('\n').at(-1)+' | início real: '+(success?hh(Number(read('ciclo.manha'))):'não confirmado'));
   if(!success)alert('Falha ao abrir/conferir janela após 3 tentativas');return;
 }
 if(!m.reset||m.reset<=t){close();return;}
 if(m.reset<early&&t>=m.reset-900)once(`ciclo.aviso-${a}-${m.reset}`,()=>{run(`${bin}/modo_economia`,[hh(pending)]);log('aviso R-15: modo_economia até '+hh(pending));});
 if(m.reset>late&&t<early){put('PORTA_FECHADA',hh(early));escapeWorking();once(`ciclo.perdido-${a}`,()=>alert('Janela começou depois do corte; porta segue fechada até '+hh(early)));return;}
 if(t>=m.reset-600){put('PORTA_FECHADA',hh(pending));log('porta fechada até '+hh(pending));escapeWorking();}else{del('PORTA_FECHADA');log('janela ativa; porta aberta');}
}

try{
 const [mode,arg,value]=process.argv.slice(2);
 if(mode==='cli'){
   if(arg==='--ancora'&&/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value||'')){put('ciclo.conf',`ANCORA=${value}\nTOL=${tol()/60}`);del('ciclo.pendente');console.log(`Âncora: ${value}`);}
   else if(arg==='--tol'&&/^\d+$/.test(value||'')&&Number(value)<150){put('ciclo.conf',`ANCORA=${conf()}\nTOL=${value}`);del('ciclo.pendente');console.log(`Tolerância: ${value} min`);}
   else if(arg==='--plano'){plan();}
   else if(arg==='--liberar'){put('CICLO_LIBERADO',anchors(now()).next);del('PORTA_FECHADA');console.log(`Liberado até ${conf()}`);}
   else if(arg==='--status'){expire(now());console.log(`Âncora: ${conf()} | TOL: ${tol()/60} min | porta: ${fs.existsSync(file('PORTA_FECHADA'))?'fechada':'aberta'} | liberação: ${read('CICLO_LIBERADO','não')}`);}
   else{console.error('Uso: ciclo --ancora HH:MM | --tol MIN | --plano | --liberar | --status');process.exitCode=2;}
 }else if(arg==='--plano')plan();else if(arg==='--teste')process.exitCode=daily();else await control();
}catch(e){console.error(e.message);process.exitCode=1;}
