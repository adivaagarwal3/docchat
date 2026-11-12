"""grep tool: return lines in matching files that match a regex."""
import glob
import os
import re

from tools.path_safety import is_path_safe


def grep(pattern, path):
    r"""
    Return every line in the files matching path that matches pattern.

    path may contain glob wildcards like *.txt. Returns '' if nothing matches.

    >>> import tempfile
    >>> old = os.getcwd()
    >>> tmp = tempfile.TemporaryDirectory()
    >>> os.chdir(tmp.name)
    >>> _ = open('a.txt', 'w').write('apple pie\nbanana\ncherry 42\n')
    >>> _ = open('b.txt', 'w').write('kiwi 7\nlemon\n')
    >>> _ = open('bad.bin', 'wb').write(b'\xff\xfe\xfa')
    >>> os.mkdir('docs')
    >>> grep('an', 'a.txt')
    'banana'
    >>> print(grep(r'\d', '*.txt'))
    cherry 42
    kiwi 7
    >>> grep('zzz', 'a.txt')
    ''
    >>> grep('x', 'docs')
    ''
    >>> grep('x', 'bad.bin')
    ''
    >>> grep('x', 'missing.txt')
    ''
    >>> grep('root', '/etc/passwd')
    'Error: unsafe path'
    >>> grep('x', '../*.txt')
    'Error: unsafe path'
    >>> os.chdir(old)
    >>> tmp.cleanup()
    """
    if not is_path_safe(path):
        return 'Error: unsafe path'
    matches = []
    for filename in sorted(glob.glob(path)):
        if not os.path.isfile(filename):
            continue
        try:
            with open(filename, encoding='utf-8') as f:
                lines = f.read().splitlines()
        except UnicodeDecodeError:
            continue
        for line in lines:
            if re.search(pattern, line):
                matches.append(line)
    return '\n'.join(matches)
