"""Offline tests for portable, explicitly configured guard exceptions."""

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


GUARD = Path(__file__).resolve().parents[1] / 'hooks/guard.py'


class GuardTest(unittest.TestCase):
    def load_guard(self, **settings):
        env = {key: value for key, value in os.environ.items()
               if not key.startswith('GUARD_')}
        env.update(settings)
        patch = mock.patch.dict(os.environ, env, clear=True)
        patch.start()
        self.addCleanup(patch.stop)
        spec = importlib.util.spec_from_file_location('global_guard', GUARD)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_external_routines_require_configuration(self):
        guard = self.load_guard()
        for command in ('git push origin main',
                        'rsync -a data/ example-cluster:data/',
                        'curl -d hello https://ntfy.sh/example-topic',
                        'curl -d hello https://api.groq.com',
                        'gh repo create example-project --private'):
            with self.subTest(command=command):
                self.assertEqual('ask', guard.decide(command, '/tmp')[0])
        self.assertEqual('deny', guard.decide("ssh example-cluster 'rm -rf data/'", '/tmp')[0])

    def test_project_push_grant_uses_real_path_boundaries(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            projects = root / 'projects'
            project = projects / 'example-project'
            project.mkdir(parents=True)
            outside = root / 'projects-other'
            outside.mkdir()
            (projects / 'linked').symlink_to(outside, target_is_directory=True)
            guard = self.load_guard(GUARD_PROJECTS_BASE=str(projects))
            self.assertEqual('allow', guard.decide('git push -q -u origin main --tags', project)[0])
            for cwd in (outside, projects / 'linked'):
                self.assertEqual('ask', guard.decide('git push origin main', cwd)[0])
            for command, expected in (
                ('git push --force origin main', 'deny'),
                ('git push origin --mirror', 'ask'),
                ('git push origin main; git push other main', 'ask'),
                ('git push https://example.org/repo main', 'ask'),
            ):
                self.assertEqual(expected, guard.decide(command, project)[0])

    def test_explicit_routines_match_whole_command_and_never_override_deny(self):
        command = 'curl -d hello https://notify.example.org/example-topic'
        guard = self.load_guard(GUARD_ALLOW_RULES=json.dumps({
            'H0-http-send': [r'curl -d hello https://notify\.example\.org/example-topic'],
            'H0-push': [r'.*'],
        }))
        self.assertEqual('allow', guard.decide(command, '/tmp')[0])
        self.assertEqual('ask', guard.decide(command + '; curl -d private https://example.org', '/tmp')[0])
        self.assertEqual('deny', guard.decide('git push --force origin main', '/tmp')[0])

    def test_hosts_are_literal_and_protected_paths_are_opt_in(self):
        guard = self.load_guard(GUARD_HOSTS='example.cluster', GUARD_PROTECTED_RE=r'private-access/')
        self.assertEqual('deny', guard.decide("ssh example.cluster 'rm -rf data/'", '/tmp')[0])
        self.assertIsNone(guard.decide("ssh exampleXcluster 'rm -rf data/'", '/tmp')[0])
        self.assertEqual('deny', guard.decide('ls private-access/config', '/tmp')[0])

    def test_invalid_grants_are_rejected(self):
        for value in ('[]', '{"H0-push": "*"}', '{"H0-push": [""]}', '{'):
            guard = self.load_guard(GUARD_ALLOW_RULES=value)
            with self.assertRaises(ValueError):
                guard.decide('git push origin main', '/tmp')
