"""ls tool: list the files in a folder."""
import glob
import os

from tools.path_safety import is_path_safe


def ls(path='.'):
    """
    Return a sorted, newline-separated list of the entries in path.

    With no argument, list the current folder.

    >>> import tempfile
    >>> old = os.getcwd()
    >>> tmp = tempfile.TemporaryDirectory()
    >>> os.chdir(tmp.name)
    >>> for name in ['b.txt', 'a.txt']:
    ...     _ = open(name, 'w').write('hi')
    >>> os.mkdir('docs')
    >>> _ = open('docs/c.md', 'w').write('hi')
    >>> print(ls())
    a.txt
    b.txt
    docs
    >>> print(ls('docs'))
    docs/c.md
    >>> ls('nonexistent_folder')
    ''
    >>> ls('/etc')
    'Error: unsafe path'
    >>> ls('../')
    'Error: unsafe path'
    >>> os.chdir(old)
    >>> tmp.cleanup()
    """
    if not is_path_safe(path):
        return 'Error: unsafe path'
    pattern = '*' if path == '.' else os.path.join(path, '*')
    return '\n'.join(sorted(glob.glob(pattern)))
