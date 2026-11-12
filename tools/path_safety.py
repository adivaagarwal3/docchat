"""Shared path-safety check used by every file-reading tool."""
import os


def is_path_safe(path):
    """
    Return True only if path is relative and does not contain '..'.

    >>> is_path_safe('notes.txt')
    True
    >>> is_path_safe('docs/notes.txt')
    True
    >>> is_path_safe('*.py')
    True
    >>> is_path_safe('/etc/passwd')
    False
    >>> is_path_safe('../secret.txt')
    False
    >>> is_path_safe('docs/../../secret.txt')
    False
    """
    if os.path.isabs(path):
        return False
    if '..' in path:
        return False
    return True
