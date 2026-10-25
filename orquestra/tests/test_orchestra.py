"""Offline orchestration tests: fake herdr, temporary handoff and mocked HTTP."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('orchestra', ROOT / 'orchestra.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OrchestraTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / 'projects/proj-a'
        self.project.mkdir(parents=True)
        self.agent = {'agent': 'claude', 'agent_status': 'idle', 'pane_id': 'w1:p1',
                      'cwd': str(self.project), 'agent_session': {'value': 'session-a'}}
        self.pool = self.root / 'agents.json'
        self.pool.write_text(json.dumps({'result': {'agents': [self.agent]}}))
        self.fake = self.root / 'herdr'
        self.fake.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
root = pathlib.Path(os.environ['FAKE_ROOT'])
args = sys.argv[1:]
if args[:2] == ['agent', 'list']:
    print((root / 'agents.json').read_text())
elif args[:2] == ['agent', 'read']:
    print('You hit your usage limit\\n────────────────\\n❯ \\n────────────────')
elif args[:2] == ['agent', 'prompt']:
    with (root / 'prompts.jsonl').open('a') as f:
        f.write(json.dumps(args) + '\\n')
else:
    sys.exit(1)
''')
        self.fake.chmod(0o755)
        env = {'ORCHESTRA_STATE': str(self.root / 'state'), 'ORCHESTRA_PROJECTS': str(self.root / 'projects'),
               'HERDR_BIN': str(self.fake), 'FAKE_ROOT': str(self.root),
               'ORCHESTRA_TRANSCRIPTS': str(self.root / 'transcripts'), 'NTFY_TOPIC': '',
               'ORCHESTRA_WATCH_INTERVAL': '0', 'SEND_SAMPLE_SECONDS': '0', 'MGE_LANG': 'en',
               'ORCHESTRA_JOB_STATE': str(self.root / 'jobs.json')}
        (self.root / 'jobs.json').write_text('{"jobs": []}')
        self.patch = mock.patch.dict(os.environ, env)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def prompts(self):
        path = self.root / 'prompts.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_mode_and_cli_wrapper(self):
        result = subprocess.run([str(ROOT / 'bin/modo'), 'ausente'], capture_output=True, text=True)
        self.assertEqual(0, result.returncode)
        self.assertEqual('away', json.loads((self.root / 'state/mode.json').read_text()))
        with self.assertRaises(ValueError):
            MODULE.mode('other')

    def test_resume_skips_working_and_dry_run(self):
        MODULE.resume('all', 'never', None, True, True)
        self.assertEqual([], self.prompts())
        MODULE.resume('all', 'never', None, True, False)
        self.assertEqual(1, len(self.prompts()))
        self.agent['agent_status'] = 'working'
        self.pool.write_text(json.dumps({'result': {'agents': [self.agent]}}))
        MODULE.resume('all', 'never', None, True, False)
        self.assertEqual(1, len(self.prompts()))

    def test_watcher_events_connectivity_and_busy_retry(self):
        script = self.project / 'vigia_status.sh'
        script.write_text('#!/bin/sh\necho "! completed"\necho "progress 1"\n')
        script.chmod(0o755)
        MODULE.watcher()
        script.write_text('#!/bin/sh\necho "! completed"\necho "progress 2"\n')
        MODULE.watcher()
        self.assertEqual(1, len(self.prompts()))
        script.write_text('#!/bin/sh\necho "no connection"; exit 1\n')
        MODULE.watcher()
        MODULE.watcher()
        self.assertEqual(1, len(self.prompts()))
        MODULE.watcher()
        self.assertEqual(2, len(self.prompts()))
        self.agent['agent_status'] = 'working'
        self.pool.write_text(json.dumps({'result': {'agents': [self.agent]}}))
        script.write_text('#!/bin/sh\necho "! new job done"\n')
        MODULE.watcher()
        self.assertEqual(2, len(self.prompts()))
        self.agent['agent_status'] = 'idle'
        self.pool.write_text(json.dumps({'result': {'agents': [self.agent]}}))
        MODULE.watcher()
        self.assertEqual(3, len(self.prompts()))

    def test_handoff_nested_paths_and_symlink_rejection(self):
        folder = self.project / '_handoff'
        (folder / 'docs').mkdir(parents=True)
        (folder / 'docs/result.md').write_text('synthetic')
        with contextlib.redirect_stdout(io.StringIO()) as output:
            MODULE.list_handoff()
        self.assertEqual('proj-a|docs/result.md\n', output.getvalue())
        with self.assertRaises(ValueError):
            MODULE.archive_handoff('batch-a', 'proj-a|../../escape')
        self.assertTrue((folder / 'docs/result.md').exists())
        MODULE.archive_handoff('batch-a', 'proj-a|docs/result.md')
        self.assertTrue((folder / '.sent/batch-a/docs/result.md').exists())
        (folder / 'link').symlink_to(self.root)
        with self.assertRaises(ValueError):
            MODULE.archive_handoff('batch-b', 'proj-a|link/agents.json')

    def test_idle_sessions_protect_missing_state_and_explicit_close(self):
        transcript = self.root / 'transcripts/proj-a/session-a.jsonl'
        transcript.parent.mkdir(parents=True)
        transcript.touch()
        os.utime(transcript, (time.time() - 90000, time.time() - 90000))
        MODULE.idle_sessions(True)
        self.assertEqual([], self.prompts())
        (self.project / 'state').mkdir()
        (self.project / 'state/current.json').write_text('{"running": false}')
        MODULE.idle_sessions(False)
        self.assertEqual([], self.prompts())
        (self.root / 'jobs.json').write_text(json.dumps({'jobs': [{'pid': os.getpid(), 'cwd': str(self.project)}]}))
        MODULE.idle_sessions(True)
        self.assertEqual([], self.prompts())
        (self.root / 'jobs.json').write_text('{"jobs": []}')
        MODULE.idle_sessions(True)
        self.assertEqual('/exit', self.prompts()[0][-1])
        with mock.patch.dict(os.environ, {'ORCHESTRA_EXCLUDE': 'w1:p1'}):
            MODULE.idle_sessions(True)
        self.assertEqual(1, len(self.prompts()))

    def test_ntfy_quiet_hours_and_groq_environment_only(self):
        self.assertEqual('low', MODULE.priority('high', 23))
        self.assertEqual('low', MODULE.priority('alta', 7))
        self.assertEqual('high', MODULE.priority('alta', 12))
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = b'{"choices": [{"message": {"content": "synthetic answer"}}]}'
        with mock.patch.dict(os.environ, {'NTFY_TOPIC': 'example-topic', 'GROQ_API_KEY': 'synthetic-test-value', 'GROQ_MODEL': 'example-model'}), mock.patch.object(MODULE.urllib.request, 'urlopen', return_value=response) as request:
            MODULE.notify('example', 'synthetic', 'high')
            MODULE.groq('summarize', None, 'a' * 20000)
            data = json.loads(request.call_args.args[0].data)
            self.assertLessEqual(len(data['messages'][0]['content']), 12020)
            self.assertEqual('example-model', data['model'])


if __name__ == '__main__':
    unittest.main()
