#!/usr/bin/env python3
"""Regression tests for the Edge profile boundary; no browser is contacted."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import agent_edge


PROFILE = '/tmp/Edge Automation'
EXE = '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'
LINUX_EXE = '/opt/microsoft/msedge/msedge'


class ProfileBindingTests(unittest.TestCase):
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

    def test_linux_browser_process_is_accepted(self):
        agent_edge.verify_profile(
            [LINUX_EXE, '--user-data-dir=' + PROFILE, '--remote-debugging-address=127.0.0.1',
             '--remote-debugging-port=9223'], PROFILE, 9223)
        with self.assertRaises(ValueError):
            agent_edge.verify_profile(
                ['/usr/bin/other', '--user-data-dir=' + PROFILE, '--remote-debugging-port=9223'],
                PROFILE, 9223)

    def test_linux_flattened_process_title_is_split_on_spaces(self):
        title = f'{LINUX_EXE} --user-data-dir={PROFILE.replace(" ", "")} --remote-debugging-port=9223'
        with patch.object(agent_edge.sys, 'platform', 'linux'), \
             patch.object(agent_edge.Path, 'read_bytes', return_value=title.encode() + b'\0'):
            args = agent_edge.process_argv(1)
        self.assertEqual(args, title.split())
        agent_edge.verify_profile(args, PROFILE.replace(' ', ''), 9223)
        with self.assertRaises(ValueError):
            agent_edge.verify_profile(args, PROFILE, 9223)

    @unittest.skipUnless(sys.platform in ('darwin',) or sys.platform.startswith('linux'),
                         'native argument readers exist for macOS and Linux')
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
