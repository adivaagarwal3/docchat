r"""docchat: a chatbot that answers questions about the files in a folder.

Run ``chat`` (after ``pip install -e .``) or ``python chat.py`` to start it.
The model can call the ls, cat, grep, and calculate tools on its own.
Lines starting with ``/`` run a tool directly, e.g. ``/ls .`` or
``/grep "def " *.py``, and add its output to the conversation.
"""
import json
import os
import shlex

from dotenv import load_dotenv

from tools.calculate import calculate
from tools.cat import cat
from tools.grep import grep
from tools.ls import ls

MODEL = 'openai/gpt-oss-20b'
TIMEOUT = 30

SYSTEM_PROMPT = (
    'You are a helpful assistant that answers questions about the files '
    'in the current folder. Use the ls, cat, and grep tools to look at the '
    'files before answering, and the calculate tool for arithmetic. '
    'Only use relative paths.'
)

TOOLS = {
    'ls': ls,
    'cat': cat,
    'grep': grep,
    'calculate': calculate,
}

TOOL_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'ls',
            'description': 'List the files in a folder (default: current folder).',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Relative folder path.'},
                },
                'required': [],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'cat',
            'description': 'Return the contents of a text file.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'path': {'type': 'string', 'description': 'Relative file path.'},
                },
                'required': ['path'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'grep',
            'description': 'Return lines matching a regex in files matching a path or glob.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'pattern': {'type': 'string', 'description': 'Python regular expression.'},
                    'path': {'type': 'string', 'description': 'Relative path or glob, e.g. *.py.'},
                },
                'required': ['pattern', 'path'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'calculate',
            'description': 'Evaluate an arithmetic expression like (2 + 3) * 4.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'expression': {'type': 'string', 'description': 'Arithmetic expression.'},
                },
                'required': ['expression'],
            },
        },
    },
]


class _FakeClient:
    """A stand-in for the Groq client, for tests.

    Each reply is either a string (the model answers in plain text) or a
    ``(tool_name, arguments)`` tuple (the model requests a tool call).
    Every request's messages are copied into ``sent``.

    >>> sent = []
    >>> client = _FakeClient(['Ahoy!', ('ls', {})], sent)
    >>> client.chat.completions.create(messages=[{'role': 'user', 'content': 'Hi'}]
    ...     ).choices[0].message.content
    'Ahoy!'
    >>> call = client.chat.completions.create(messages=[]).choices[0].message.tool_calls[0]
    >>> call.id, call.function.name, call.function.arguments
    ('call_2', 'ls', '{}')
    >>> sent
    [[{'role': 'user', 'content': 'Hi'}], []]
    """

    def __init__(self, replies, sent):
        """Store the scripted replies and the list that records requests."""
        self.replies = list(replies)
        self.sent = sent
        self.chat = self
        self.completions = self

    def create(self, messages, **kwargs):
        """Record the messages sent and return the next scripted reply."""
        from types import SimpleNamespace as NS
        self.sent.append([dict(m) for m in messages])
        reply = self.replies.pop(0)
        if isinstance(reply, str):
            message = NS(content=reply, tool_calls=None)
        else:
            name, args = reply
            call = NS(id=f'call_{len(self.sent)}', type='function',
                      function=NS(name=name, arguments=json.dumps(args)))
            message = NS(content=None, tool_calls=[call])
        return NS(choices=[NS(message=message)])


def run_tool(name, arguments):
    """Run the tool called name with JSON-encoded arguments; return its output.

    >>> run_tool('calculate', '{"expression": "6 * 7"}')
    '42'
    >>> run_tool('cat', '{"path": "/etc/passwd"}')
    'Error: unsafe path'
    >>> run_tool('rm', '{}')
    'Error: unknown tool rm'
    >>> run_tool('cat', '{"wrong": "x"}')
    'Error: bad arguments for cat'
    >>> run_tool('cat', 'not json')
    'Error: bad arguments for cat'
    """
    if name not in TOOLS:
        return f'Error: unknown tool {name}'
    try:
        args = json.loads(arguments or '{}')
        return TOOLS[name](**args)
    except (TypeError, ValueError):
        return f'Error: bad arguments for {name}'


def _message_to_dict(message):
    """Convert an assistant message object into a dict for the history.

    Keeps the tool calls, not just the text.

    >>> sent = []
    >>> client = _FakeClient([('cat', {'path': 'a.txt'}), 'Done.'], sent)
    >>> msg = client.chat.completions.create(messages=[]).choices[0].message
    >>> _message_to_dict(msg) == {
    ...     'role': 'assistant', 'content': None,
    ...     'tool_calls': [{'id': 'call_1', 'type': 'function',
    ...                     'function': {'name': 'cat',
    ...                                  'arguments': '{"path": "a.txt"}'}}]}
    True
    >>> msg = client.chat.completions.create(messages=[]).choices[0].message
    >>> _message_to_dict(msg)
    {'role': 'assistant', 'content': 'Done.'}
    """
    entry = {'role': 'assistant', 'content': message.content}
    if message.tool_calls:
        entry['tool_calls'] = [
            {
                'id': call.id,
                'type': 'function',
                'function': {
                    'name': call.function.name,
                    'arguments': call.function.arguments,
                },
            }
            for call in message.tool_calls
        ]
    return entry


class Chat:
    r"""A conversation that keeps its full history and can call tools.

    >>> Chat(system='Be brief.').messages
    [{'role': 'system', 'content': 'Be brief.'}]

    The API client is only created when a chat message is sent, never at
    import time or when a Chat is made:

    >>> from unittest.mock import patch
    >>> with patch('groq.Groq') as Groq:
    ...     chat = Chat()
    ...     Groq.call_count
    ...     first = chat.client
    ...     chat.client is first, Groq.call_count
    0
    (True, 1)

    When the model requests a tool, the tool runs and its result goes back
    to the model with the matching tool_call_id:

    >>> import os, tempfile
    >>> old = os.getcwd()
    >>> tmp = tempfile.TemporaryDirectory()
    >>> os.chdir(tmp.name)
    >>> _ = open('notes.txt', 'w').write('hello')
    >>> sent = []
    >>> chat = Chat(system='Be brief.',
    ...             client=_FakeClient([('ls', {}), 'There is one file.'], sent))
    >>> chat.send_message('What files are here?', temperature=0)
    'There is one file.'
    >>> len(sent)
    2
    >>> sent[1][-1]
    {'role': 'tool', 'tool_call_id': 'call_1', 'content': 'notes.txt'}
    >>> sent[1][-2]['tool_calls'][0]['id']
    'call_1'
    >>> [m['role'] for m in chat.messages]
    ['system', 'user', 'assistant', 'tool', 'assistant']
    >>> chat.messages[-1]
    {'role': 'assistant', 'content': 'There is one file.'}
    >>> os.chdir(old)
    >>> tmp.cleanup()
    """

    def __init__(self, system=SYSTEM_PROMPT, client=None):
        """Start the history with a system message; the client is made later."""
        self.messages = [{'role': 'system', 'content': system}]
        self._client = client

    @property
    def client(self):
        """Create the Groq client on first use, then reuse it."""
        if self._client is None:
            from groq import Groq
            load_dotenv()
            self._client = Groq(api_key=os.environ.get('GROQ_API_KEY'),
                                timeout=TIMEOUT)
        return self._client

    def send_message(self, message, temperature=0.8):
        """Send a message, run any tools the model asks for, and return the reply.

        A plain exchange stores the user message and the reply:

        >>> sent = []
        >>> chat = Chat(system='Be brief.', client=_FakeClient(['Hello!'], sent))
        >>> chat.send_message('Hi', temperature=0)
        'Hello!'
        >>> chat.messages[1:]
        [{'role': 'user', 'content': 'Hi'}, {'role': 'assistant', 'content': 'Hello!'}]
        """
        self.messages.append({'role': 'user', 'content': message})
        while True:
            completion = self.client.chat.completions.create(
                messages=self.messages,
                model=MODEL,
                tools=TOOL_SCHEMAS,
                temperature=temperature,
                timeout=TIMEOUT,
            )
            reply = completion.choices[0].message
            self.messages.append(_message_to_dict(reply))
            if not reply.tool_calls:
                return reply.content
            for call in reply.tool_calls:
                self.messages.append({
                    'role': 'tool',
                    'tool_call_id': call.id,
                    'content': run_tool(call.function.name, call.function.arguments),
                })


def run_command(chat, line):
    """Run a manual /command, add its output to the chat, and return it.

    No API request is made.

    >>> chat = Chat(system='Be brief.')
    >>> run_command(chat, '/calculate 2+2')
    '4'
    >>> chat.messages[-1]
    {'role': 'user', 'content': 'Output of /calculate 2+2:\\n4'}
    >>> run_command(chat, '/grep "a b" /etc/passwd')
    'Error: unsafe path'
    >>> run_command(chat, '/rm x')
    'Error: unknown command /rm'
    >>> run_command(chat, '/cat')
    'Error: bad arguments for /cat'
    >>> run_command(chat, '/')
    'Error: empty command'
    >>> run_command(chat, '/cat "unclosed')
    'Error: bad arguments for /cat'
    >>> chat._client is None
    True
    """
    try:
        parts = shlex.split(line[1:])
    except ValueError:
        parts = None
    if parts == []:
        output = 'Error: empty command'
    elif parts is None:
        output = f'Error: bad arguments for /{line[1:].split()[0]}'
    elif parts[0] not in TOOLS:
        output = f'Error: unknown command /{parts[0]}'
    else:
        try:
            output = TOOLS[parts[0]](*parts[1:])
        except TypeError:
            output = f'Error: bad arguments for /{parts[0]}'
    chat.messages.append({'role': 'user', 'content': f'Output of {line}:\n{output}'})
    return output


def repl(temperature=0.8):
    r"""Read input and reply until Ctrl-C or end of input.

    Lines starting with / run a tool directly, with no API request:

    >>> import os, tempfile
    >>> from unittest.mock import patch
    >>> old = os.getcwd()
    >>> tmp = tempfile.TemporaryDirectory()
    >>> os.chdir(tmp.name)
    >>> _ = open('notes.txt', 'w').write('hello')
    >>> with patch('builtins.input', side_effect=['/ls .', EOFError]), \
    ...      patch('groq.Groq') as Groq:
    ...     repl(temperature=0)
    notes.txt
    <BLANKLINE>
    >>> Groq.call_count
    0

    Ordinary lines go to the model, which may call tools on its own:

    >>> sent = []
    >>> fake = _FakeClient([('cat', {'path': 'notes.txt'}), 'It says hello.'], sent)
    >>> with patch('builtins.input', side_effect=['What does notes.txt say?',
    ...                                           KeyboardInterrupt]), \
    ...      patch('groq.Groq', return_value=fake):
    ...     repl(temperature=0)
    It says hello.
    <BLANKLINE>
    >>> sent[1][-1]
    {'role': 'tool', 'tool_call_id': 'call_1', 'content': 'hello'}
    >>> os.chdir(old)
    >>> tmp.cleanup()
    """
    chat = Chat()
    try:
        while True:
            user_input = input('chat> ')
            if user_input.startswith('/'):
                print(run_command(chat, user_input))
            else:
                print(chat.send_message(user_input, temperature=temperature))
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == '__main__':
    repl()
