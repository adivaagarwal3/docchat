"""cat tool: return the contents of a file."""
from tools.path_safety import is_path_safe


def cat(path):
    """
    Return the text contents of the file at path.

    >>> import os, tempfile
    >>> old = os.getcwd()
    >>> tmp = tempfile.TemporaryDirectory()
    >>> os.chdir(tmp.name)
    >>> _ = open('hello.txt', 'w').write('hello world\\nline two\\n')
    >>> print(cat('hello.txt'), end='')
    hello world
    line two
    >>> _ = open('bad.bin', 'wb').write(b'\\xff\\xfe\\xfa')
    >>> cat('bad.bin')
    'Error: bad.bin is not valid UTF-8 text'
    >>> cat('missing.txt')
    'Error: missing.txt not found'
    >>> cat('/etc/passwd')
    'Error: unsafe path'
    >>> cat('../secret.txt')
    'Error: unsafe path'
    >>> os.chdir(old)
    >>> tmp.cleanup()
    """
    if not is_path_safe(path):
        return 'Error: unsafe path'
    try:
        with open(path, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f'Error: {path} not found'
    except UnicodeDecodeError:
        return f'Error: {path} is not valid UTF-8 text'
