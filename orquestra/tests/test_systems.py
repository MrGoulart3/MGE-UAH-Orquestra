"""Offline tests for credit doors, communication, grants and queue serialization."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import clusters
import night_priority


class SystemsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.state.mkdir()
        self.cache = self.root / 'usage.json'
        self.cache.write_text(json.dumps({'timestamp':time.time()*1000,'data':{'fiveHourPercent':80,'fiveHourResetsAt':'2026-10-24T20:00:00Z'}}))
        self.env = os.environ | {'ORCHESTRA_STATE':str(self.state),'USAGE_CACHE':str(self.cache),
            'ORCHESTRA_BIN':str(ROOT/'bin'),'SEND_SAMPLE_SECONDS':'0','TZ':'UTC',
            'ORCHESTRA_COORDINATOR':'w1:p1','ORCHESTRA_CONFIG':''}
        self.patch = mock.patch.dict(os.environ,self.env)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def call(self, name, *args, body=None, **env):
        return subprocess.run([str(ROOT/'bin'/name),*args],env=self.env|env,input=body,
                              capture_output=True,text=True,timeout=10)

    def fake(self, content):
        path = self.root/'herdr'
        path.write_text('#!/usr/bin/env python3\n'+content)
        path.chmod(0o755)
        self.env['HERDR_BIN'] = str(path)

    def test_hook_closed_direct_message_and_expired_release(self):
        (self.state/'PORTA_FECHADA').write_text('05:00')
        result = self.call('ciclo_porta_hook',body='{"prompt":"routine"}')
        self.assertEqual(json.loads(result.stdout)['decision'],'block')
        self.assertEqual(self.call('ciclo_porta_hook',body='{"prompt":"Operator: continue"}').stdout,'')
        (self.state/'CICLO_LIBERADO').write_text('1')
        self.assertIn('block', self.call('ciclo_porta_hook',body='{"prompt":"routine"}').stdout)
        self.assertFalse((self.state/'CICLO_LIBERADO').exists())

    def test_messages_working_agent_is_queued_and_unknown_ui_is_not_sent(self):
        self.fake('import sys,json\nprint(json.dumps({"result":{"agents":[{"pane_id":"w2:p1","agent_status":"working"}]}}))\n')
        result = self.call('enviar_space','w2:p1','hello','0')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(list((self.state/'recados_pendentes').glob('*.txt'))),1)
        result = self.call('enviar_space','w2:p1','retry','0',NAO_GUARDAR='1')
        self.assertEqual(result.returncode,3)
        self.fake('import sys,json\nif sys.argv[1:3]==["agent","list"]: print(json.dumps({"result":{"agents":[]}}))\nelse: print("unknown screen")\n')
        self.assertEqual(self.call('enviar_space','w2:p1','hello','0',NAO_GUARDAR='1').returncode,2)

    def test_meter_cache_does_not_require_optional_usage_module(self):
        result = self.call('medidor',MEDIDOR_SO_CACHE='1')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.split()[0],'80')

    def test_cluster_grants_reserve_capacity_and_dry_run_preserves_requests(self):
        cfg={'clusters':{'batch':{'measure_command':['fake'],'max_cores':4,'max_memory_gb':8}},'priority':['sample-a']}
        rows=[clusters.request('sample-a',['batch','3','2','job-a'],cfg),clusters.request('sample-b',['batch','3','2','job-b'],cfg)]
        clusters.orchestra.save(clusters.requests_path(),rows)
        pool=[dict(agent='claude',agent_status='idle',pane_id=f'w{i}:p1',cwd=f'/srv/projects/sample-{c}') for i,c in [(2,'a'),(3,'b')]]
        snapshot=dict(timestamp=time.time(),used_cores=0,used_memory_gb=0,load=0,jobs=0)
        with mock.patch.object(clusters,'measure',side_effect=lambda _:snapshot.copy()), mock.patch.object(clusters.orchestra,'agents',return_value=pool), mock.patch.object(clusters,'send',return_value=True) as send:
            clusters.grants(cfg,True)
            self.assertEqual(clusters.read_requests(),rows)
            send.assert_not_called()
            clusters.grants(cfg,False)
            self.assertEqual(send.call_count,1)
            self.assertEqual([r['name'] for r in clusters.read_requests()],['job-b'])
            clusters.grants(cfg,False)
            self.assertEqual(send.call_count,1)

    def test_bad_or_stale_measurement_is_rejected(self):
        for data in [dict(timestamp=0,used_cores=0,used_memory_gb=0,load=0,jobs=0),dict(timestamp=time.time(),used_cores=-1,used_memory_gb=0,load=0,jobs=0)]:
            with mock.patch.object(clusters.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(data))):
                with self.assertRaises(ValueError):
                    clusters.measure({'measure_command':['fake']})

    def test_priority_queue_waits_for_completion_even_after_timeout(self):
        directory=self.state/'night-priority'
        directory.mkdir()
        (directory/'active.json').write_text(json.dumps(dict(space='sample-a',started=0)))
        (directory/'queue.json').write_text(json.dumps([dict(space='sample-b',pane='w2:p1')]))
        with mock.patch.object(night_priority.subprocess,'run') as run:
            night_priority.tick({'state_dir':str(self.state)})
            run.assert_not_called()
        self.assertTrue((directory/'active.json').exists())

    def test_cycle_morning_cap_and_night_cut_without_real_calls(self):
        fakebin=self.root/'bin'
        fakebin.mkdir()
        # Only the meter and agent listing are consulted in these branches.
        for name,body in {'medidor':'echo "35 2026-10-24T10:00:00Z 0"','herdr':'''echo '{"result":{"agents":[]}}' '''}.items():
            p=fakebin/name;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o755)
        (self.state/'ciclo.conf').write_text('ANCORA=05:00\nTOL=1\n')
        (self.state/'ciclo.manha').write_text('1792818000')
        import datetime
        morning=int(datetime.datetime(2026,10,24,5,tzinfo=datetime.timezone.utc).timestamp())
        (self.state/'ciclo.manha').write_text(str(morning))
        env=self.env|{'ORCHESTRA_BIN':str(fakebin),'PATH':str(fakebin)+os.pathsep+os.environ['PATH'],'AGORA':str(morning+3600)}
        result=subprocess.run(['node',str(ROOT/'bin/ciclo_core.mjs'),'controle'],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('teto', (self.state/'PORTA_FECHADA').read_text())
        self.assertTrue((self.state/'ciclo.teto').exists())

    def test_restart_cancellation_is_persistent_and_paths_are_validated(self):
        self.assertEqual(self.call('reiniciar_space', 'w2:p1', '--cancelar').returncode, 0)
        self.assertEqual(self.call('reiniciar_space', 'w2:p1', '--forcar').returncode, 6)
        self.assertEqual(self.call('reiniciar_space', 'w2:p1', '--liberar').returncode, 0)
        self.assertFalse((self.state / 'reinicio/w2:p1.cancelar').exists())
        self.assertNotEqual(self.call('reiniciar_space', '../escape', '--cancelar').returncode, 0)
        self.assertEqual(self.call('reiniciar_space', 'w1:p1', '--forcar').returncode, 2)

    def test_delivery_versions_and_invalid_space(self):
        source = self.root / 'sample.txt'
        source.write_text('version one')
        delivery = self.root / 'deliveries'
        args = (str(source), '--space', 'sample-a', '--sem-previa')
        self.assertEqual(self.call('deliver_file', *args, ENTREGAS_DIR=str(delivery)).returncode, 0)
        self.assertEqual(self.call('deliver_file', *args, '--substituir', ENTREGAS_DIR=str(delivery)).returncode, 0)
        events = [json.loads(line) for line in (delivery / 'indice.jsonl').read_text().splitlines()]
        self.assertEqual([r['versao'] for r in events if r['tipo'] == 'entrega'], [1, 2])
        self.assertEqual(events[-1]['tipo'], 'oculto')
        self.assertNotEqual(self.call('deliver_file', str(source), '--space', '../escape', ENTREGAS_DIR=str(delivery)).returncode, 0)

    def test_central_catalog_uses_configured_path(self):
        central = self.root / 'catalog/central.json'
        result = self.call('central_add', '--titulo', 'Sample tool', '--url', 'https://example.org/tool', '--space', 'sample-a', ORCHESTRA_CENTRAL=str(central))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(next(iter(json.loads(central.read_text()).values()))['space'], 'sample-a')

    def test_atomic_batch_validation(self):
        cfg = self.root / 'clusters.json'
        cfg.write_text(json.dumps({'clusters':{'batch':{}}}))
        batch = self.root / 'requests.txt'
        batch.write_text('batch|2|4|valid|ready\nmissing|2|4|invalid|ready\n')
        result = self.call('pedir_vaga', '--lote', 'sample-a', str(batch), ORCHESTRA_CLUSTERS=str(cfg))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.state / 'cluster-requests.json').exists())

    def test_credit_guard_preview_and_stale_cache(self):
        import datetime
        now = int(datetime.datetime(2026, 10, 24, 12, tzinfo=datetime.timezone.utc).timestamp())
        self.cache.write_text(json.dumps({'timestamp':now*1000,'data':{'fiveHourPercent':85,'fiveHourResetsAt':'2026-10-24T16:00:00Z'}}))
        self.fake('import json\nprint(json.dumps({"result":{"agents":[{"pane_id":"w2:p1","agent_status":"working","agent":"claude"}]}}))\n')
        result = self.call('trava_creditos', DRYRUN='1', AGORA=str(now))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DRYRUN -> w2:p1', result.stdout)
        self.assertFalse((self.state / 'trava_creditos.state').exists())
        result = self.call('trava_creditos', DRYRUN='1', AGORA=str(now+1300))
        self.assertNotIn('DRYRUN ->', result.stdout)
