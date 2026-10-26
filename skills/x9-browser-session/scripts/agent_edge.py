#!/usr/bin/env python3
"""Attach agent-browser to the verified Microsoft Edge automation profile on macOS or Linux.

Regression checks: python3 -m unittest discover -s this-directory -p 'test_*.py'
"""

import ctypes
import os
from pathlib import Path
import re
import struct
import subprocess
import sys


PORT = 9223
BROWSER_NAMES = {'Microsoft Edge', 'msedge'}


def profile_path():
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/Microsoft Edge Automation'
    if sys.platform.startswith('linux'):
        return Path.home() / '.config/microsoft-edge-agent'
    raise ValueError('this Edge adapter requires macOS or Linux')


def process_argv(pid):
    """Read the exact argument vector without flattening argument boundaries or logging them."""
    if sys.platform.startswith('linux'):
        data = Path(f'/proc/{pid}/cmdline').read_bytes()
        if not data.endswith(b'\0'):
            raise ValueError('truncated process arguments')
        args = [os.fsdecode(arg) for arg in data[:-1].split(b'\0')]
        if len(args) == 1:
            # Chromium rewrites its process title, so the vector arrives space-joined.
            # Splitting can only add or break switches; verify_profile rejects both.
            args = args[0].split()
        return args
    if sys.platform != 'darwin':
        raise ValueError('this Edge adapter requires macOS or Linux')
    libc = ctypes.CDLL(None, use_errno=True)
    sysctl = libc.sysctl
    sysctl.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_uint, ctypes.c_void_p,
                       ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p, ctypes.c_size_t]
    sysctl.restype = ctypes.c_int
    mib = (ctypes.c_int * 3)(1, 49, pid)  # CTL_KERN, KERN_PROCARGS2
    size = ctypes.c_size_t()
    if sysctl(mib, 3, None, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno(), 'cannot size browser arguments')
    if not 4 < size.value <= 64 * 1024 * 1024:
        raise ValueError('invalid process argument size')
    buffer = ctypes.create_string_buffer(size.value)
    if sysctl(mib, 3, buffer, ctypes.byref(size), None, 0) != 0:
        raise OSError(ctypes.get_errno(), 'cannot read browser arguments')
    data = buffer.raw[:size.value]
    argc = struct.unpack_from('i', data)[0]
    position = data.find(b'\0', 4)
    if argc < 1 or argc > len(data) or position == -1:
        raise ValueError('invalid process argument header')
    while position < len(data) and data[position] == 0:
        position += 1
    args = []
    for _ in range(argc):
        end = data.find(b'\0', position)
        if end == -1:
            raise ValueError('truncated process arguments')
        args.append(os.fsdecode(data[position:end]))
        position = end + 1
    return args


def verify_profile(args, profile, port):
    """Reject missing, duplicate or prefix-matching browser switches."""
    if not args or Path(args[0]).name not in BROWSER_NAMES:
        raise ValueError('listener is not the Microsoft Edge browser process')
    expected = {'user-data-dir': str(profile), 'remote-debugging-port': str(port)}
    found = {name: [] for name in expected}
    # Chromium's POSIX CommandLine trims each argument, accepts '-' and '--',
    # and takes switch values only from '=' (base/command_line.cc).
    for raw_arg in args[1:]:
        arg = raw_arg.strip(' \t\r\n\v\f')
        if arg == '--':
            break
        if not arg.startswith('-'):
            continue
        switch = arg[2:] if arg.startswith('--') else arg[1:]
        name, equals, value = switch.partition('=')
        if name in expected:
            if not equals:
                raise ValueError('browser switch values require equals')
            found[name].append(value)
    if any(found[name] != [value] for name, value in expected.items()):
        raise ValueError('listener does not match the expected Edge profile and port')


def main():
    try:
        profile = profile_path()
        session = os.environ.get('AGENT_BROWSER_SESSION', '')
        if session == 'default' or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', session):
            raise ValueError('set a unique AGENT_BROWSER_SESSION for this task')
        arguments = sys.argv[1:]
        # The wrapper owns endpoint, controller session and strict tab binding.
        protected = {'--session', '--cdp', '--pin-tab', '--no-pin-tab', '--auto-connect'}
        if (not arguments or arguments[0].startswith('-') or arguments[0] == 'connect'
                or any(arg.partition('=')[0] in protected for arg in arguments)):
            raise ValueError('use a command without connection or task-binding overrides')
        result = subprocess.run(['lsof', '-nP', f'-tiTCP:{PORT}', '-sTCP:LISTEN'],
                                check=True, capture_output=True, text=True, timeout=3)
        pids = set(result.stdout.split())
        if len(pids) != 1 or not all(pid.isdecimal() and int(pid) > 0 for pid in pids):
            raise ValueError('CDP listener identity is ambiguous')
        verify_profile(process_argv(int(pids.pop())), profile, PORT)
        subprocess.run(['curl', '--noproxy', '*', '--fail', '--silent', '--show-error',
                        '--max-time', '3', '-o', os.devnull,
                        f'http://127.0.0.1:{PORT}/json/version'],
                       check=True, capture_output=True, timeout=4)
        os.execvp('agent-browser', ['agent-browser', '--session', session,
                                  '--cdp', str(PORT), '--pin-tab', *arguments])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        # Command output and process arguments may contain private profile data.
        print('Edge binding failed: check the task session, command, and browser profile; '
              f'{type(error).__name__}; no browser command was dispatched', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
