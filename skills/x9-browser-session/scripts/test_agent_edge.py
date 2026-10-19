#!/usr/bin/env python3
"""Regression tests for the Edge profile boundary; no browser is contacted."""

from pathlib import Path
import os
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import agent_edge


PROFILE = '/tmp/Edge Automation'
EXE = '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'


class ProfileBindingTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {'AGENT_BROWSER_SESSION': 'edge-task-42'})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_exact_arguments_allow_spaces_and_chromium_switch_prefixes(self):
        for args in (
            [EXE, '--user-data-dir=' + PROFILE, '--remote-debugging-port=9223'],
            [EXE, '-user-data-dir=' + PROFILE, '-remote-debugging-port=9223'],
            [EXE, ' \t--user-data-dir=' + PROFILE + '\t ', '--remote-debugging-port=9223\n'],
        ):
            with self.subTest(args=args):
                agent_edge.verify_profile(args, PROFILE, 9223)

    def test_rejects_profile_and_port_prefixes_and_ambiguous_values(self):
        for args in (
            [EXE, '--user-data-dir=' + PROFILE + '-other', '--remote-debugging-port=9223'],
            [EXE, '--user-data-dir=' + PROFILE, '--remote-debugging-port=92230'],
            [EXE, '--user-data-dir=' + PROFILE, '--remote-debugging-port=9223', '--user-data-dir=/tmp/other'],
            [EXE, '--user-data-dir=' + PROFILE, '--remote-debugging-port=9223', '--remote-debugging-port=9223'],
            [EXE, '--user-data-dir', '--remote-debugging-port=9223'],
            [EXE, '--', '--user-data-dir=' + PROFILE, '--remote-debugging-port=9223'],
            [EXE, '--title=--user-data-dir=' + PROFILE, '--remote-debugging-port=9223'],
            [EXE, '--user-data-dir=' + PROFILE, '-user-data-dir=/tmp/other', '--remote-debugging-port=9223'],
            [EXE, '--user-data-dir=' + PROFILE, ' --user-data-dir=/tmp/other', '--remote-debugging-port=9223'],
            [EXE, '--user-data-dir=' + PROFILE, '--remote-debugging-port=9223', '-remote-debugging-port=9224'],
            [EXE, '--user-data-dir=' + PROFILE, '--remote-debugging-port=9223', '\t--remote-debugging-port=9223 '],
            [EXE, '--user-data-dir', PROFILE, '--remote-debugging-port=9223'],
            [EXE, '--user-data-dir=' + PROFILE, '--remote-debugging-port', '9223'],
            [EXE, ' \t-- ', '--user-data-dir=' + PROFILE, '--remote-debugging-port=9223'],
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                agent_edge.verify_profile(args, PROFILE, 9223)

    def test_mismatched_profile_never_dispatches_browser_command(self):
        # Process discovery is an OS boundary; the actual verifier is not replaced.
        with patch.object(agent_edge.subprocess, 'run') as run, \
             patch.object(agent_edge, 'process_argv', return_value=[
                 EXE, '--user-data-dir=/tmp/wrong', '--remote-debugging-port=9223']), \
             patch.object(agent_edge.os, 'execvp') as dispatch, \
             patch('sys.stderr'):
            run.return_value.stdout = '123\n'
            self.assertEqual(agent_edge.main(), 1)
            dispatch.assert_not_called()
            self.assertEqual(run.call_count, 1, 'a bad binding must not reach curl')

    def test_verified_profile_dispatches_to_existing_cdp_endpoint(self):
        with patch.object(agent_edge.Path, 'home', return_value=Path('/tmp/test-home')), \
             patch.object(agent_edge.subprocess, 'run') as run, \
             patch.object(agent_edge, 'process_argv', return_value=[
                 EXE, '--user-data-dir=/tmp/test-home/Library/Application Support/Microsoft Edge Automation',
                 '--remote-debugging-port=9223']), \
             patch.object(agent_edge.os, 'execvp') as dispatch, \
             patch.object(sys, 'argv', ['agent-edge', 'snapshot']):
            run.return_value.stdout = '123\n'
            agent_edge.main()
            self.assertEqual(run.call_count, 2, 'discovery and endpoint check precede dispatch')
            dispatch.assert_called_once_with('agent-browser', [
                'agent-browser', '--session', 'edge-task-42', '--cdp', '9223', '--pin-tab', 'snapshot'])

    def test_missing_or_default_task_session_never_contacts_browser(self):
        for session in ('', 'default', ' ', 'bad session'):
            with self.subTest(session=session), \
                 patch.dict(os.environ, {'AGENT_BROWSER_SESSION': session}), \
                 patch.object(agent_edge.subprocess, 'run') as run, \
                 patch.object(agent_edge.os, 'execvp') as dispatch, patch('sys.stderr'):
                self.assertEqual(agent_edge.main(), 1)
                run.assert_not_called()
                dispatch.assert_not_called()

    def test_arguments_cannot_disable_task_binding(self):
        for args in (['snapshot', '--no-pin-tab'], ['snapshot', '--pin-tab=false'],
                     ['snapshot', '--session', 'default'], ['snapshot', '--session=other'],
                     ['snapshot', '--cdp', '9333'], ['snapshot', '--auto-connect'],
                     ['connect', '9333']):
            with self.subTest(args=args), patch.object(sys, 'argv', ['agent-edge', *args]), \
                 patch.object(agent_edge.subprocess, 'run') as run, \
                 patch.object(agent_edge.os, 'execvp') as dispatch, patch('sys.stderr'):
                self.assertEqual(agent_edge.main(), 1)
                run.assert_not_called()
                dispatch.assert_not_called()

    def test_controller_tab_gone_error_is_propagated_without_retry(self):
        # Replace the OS discovery boundary and external CLI, retaining real execvp.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / 'calls.jsonl'
            cli = root / 'agent-browser'
            cli.write_text(f'#!{sys.executable}\n' +
                           'import json,os,sys\n'
                           'with open(os.environ["EDGE_TEST_LOG"], "a") as f:\n'
                           '    f.write(json.dumps(sys.argv[1:])+"\\n")\n'
                           'print(json.dumps({"success":False,"code":"tab_gone"}))\n'
                           'sys.exit(1)\n')
            cli.chmod(0o755)
            script = '''import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import agent_edge
sys.argv = ['agent-edge', 'snapshot', '--json']
with patch.object(agent_edge.Path, 'home', return_value=Path('/tmp/edge-test-home')), \
     patch.object(agent_edge, 'process_argv', return_value=[
         '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
         '--user-data-dir=/tmp/edge-test-home/Library/Application Support/Microsoft Edge Automation',
         '--remote-debugging-port=9223']), \
     patch.object(agent_edge.subprocess, 'run', return_value=SimpleNamespace(stdout='123\\n')):
    raise SystemExit(agent_edge.main())
'''
            result = subprocess.run([sys.executable, '-B', '-c', script],
                                    cwd=Path(agent_edge.__file__).parent,
                                    env={**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                                         'EDGE_TEST_LOG': str(log)},
                                    text=True, capture_output=True, timeout=5)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout), {'success': False, 'code': 'tab_gone'})
            self.assertEqual([json.loads(line) for line in log.read_text().splitlines()], [[
                '--session', 'edge-task-42', '--cdp', '9223', '--pin-tab', 'snapshot', '--json']])

    @unittest.skipUnless(sys.platform == 'darwin', 'KERN_PROCARGS2 is a macOS interface')
    def test_native_argument_reader_preserves_a_spaced_argument(self):
        # Inspect only our own disposable process, never a user browser or its environment.
        import json
        import subprocess
        script = ('import agent_edge,json,os,sys; '
                  'args=agent_edge.process_argv(os.getpid()); '
                  'print(json.dumps(args[-2:]))')
        result = subprocess.run([sys.executable, '-c', script, 'path with spaces', 'tail'],
                                cwd=Path(agent_edge.__file__).parent,
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), ['path with spaces', 'tail'])


if __name__ == '__main__':
    unittest.main()
