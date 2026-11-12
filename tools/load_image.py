"""load_image tool: add a PNG image to the chat as a data URL."""
import base64

from tools.path_safety import is_path_safe


def load_image(chat, path):
    r"""
    Add the PNG at path to chat.messages as an OpenAI-style image_url.

    Unsafe, missing, or non-PNG paths return an error and leave the
    history unchanged.

    >>> import os, tempfile
    >>> from chat import Chat
    >>> old = os.getcwd()
    >>> tmp = tempfile.TemporaryDirectory()
    >>> os.chdir(tmp.name)
    >>> _ = open('pic.png', 'wb').write(b'\x89PNG\r\n\x1a\nabc')
    >>> chat = Chat(system='Be brief.')
    >>> load_image(chat, 'pic.png')
    'Loaded image pic.png'
    >>> msg = chat.messages[-1]
    >>> msg['role'], msg['content'][0]['type']
    ('user', 'image_url')
    >>> msg['content'][0]['image_url']['url']
    'data:image/png;base64,iVBORw0KGgphYmM='
    >>> load_image(chat, '/etc/x.png')
    'Error: unsafe path'
    >>> load_image(chat, '../x.png')
    'Error: unsafe path'
    >>> load_image(chat, 'missing.png')
    'Error: missing.png not found'
    >>> _ = open('notes.txt', 'w').write('hi')
    >>> load_image(chat, 'notes.txt')
    'Error: notes.txt is not a PNG'
    >>> len(chat.messages)
    2
    >>> os.chdir(old)
    >>> tmp.cleanup()
    """
    if not is_path_safe(path):
        return 'Error: unsafe path'
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        return f'Error: {path} not found'
    if not data.startswith(b'\x89PNG'):
        return f'Error: {path} is not a PNG'
    url = 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')
    chat.messages.append({
        'role': 'user',
        'content': [{'type': 'image_url', 'image_url': {'url': url}}],
    })
    return f'Loaded image {path}'
