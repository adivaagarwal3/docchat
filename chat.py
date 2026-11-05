"""A pirate chatbot that remembers the conversation.

Run ``chat`` (after ``pip install .``) or ``python chat.py`` to start it.
"""
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.environ.get('GROQ_API_KEY'))


def _fake_api(replies, sent):
    """Return a stand-in for ``client.chat.completions.create`` for tests.

    Each call copies the messages it receives into ``sent`` (so later
    appends to the history cannot change them) and returns the next reply
    in a response object shaped like the real one.

    >>> sent = []
    >>> create = _fake_api(['Ahoy!'], sent)
    >>> create(messages=[{'role': 'user', 'content': 'Hi'}],
    ...        model='m', temperature=0).choices[0].message.content
    'Ahoy!'
    >>> sent
    [[{'role': 'user', 'content': 'Hi'}]]
    """
    from unittest.mock import MagicMock
    replies = list(replies)

    def create(messages, **kwargs):
        sent.append([dict(m) for m in messages])
        response = MagicMock()
        response.choices[0].message.content = replies.pop(0)
        return response
    return create


def llm(messages, temperature=1):
    """Send messages to the model and return the reply text.

    >>> from unittest.mock import patch
    >>> sent = []
    >>> with patch.object(client.chat.completions, 'create',
    ...                   side_effect=_fake_api(['Paris.'], sent)) as create:
    ...     llm([{'role': 'user', 'content': 'Capital of France?'}], temperature=0)
    ...     create.call_args.kwargs['temperature']
    'Paris.'
    0
    """
    completion = client.chat.completions.create(
        messages=messages,
        model='openai/gpt-oss-20b',
        temperature=temperature,
    )
    return completion.choices[0].message.content


class Chat:
    """A conversation that keeps its full message history.

    >>> Chat(system='Be brief.').messages
    [{'role': 'system', 'content': 'Be brief.'}]
    """

    def __init__(self, system='You are a helpful assistant.'):
        self.messages = [{'role': 'system', 'content': system}]

    def send_message(self, message, temperature=0.8):
        """Send a message and retain the reply.

        A single exchange returns the reply and stores three messages:

        >>> from unittest.mock import patch
        >>> sent = []
        >>> with patch.object(client.chat.completions, 'create',
        ...                   side_effect=_fake_api(['Hello!', 'You said Hi.'], sent)):
        ...     chat = Chat(system='Be brief.')
        ...     print(chat.send_message('Hi', temperature=0))
        ...     print(chat.send_message('What did I say?', temperature=0))
        Hello!
        You said Hi.

        The follow-up request carries the earlier user message AND the
        earlier assistant reply, followed by the new user message:

        >>> sent[1] == [
        ...     {'role': 'system', 'content': 'Be brief.'},
        ...     {'role': 'user', 'content': 'Hi'},
        ...     {'role': 'assistant', 'content': 'Hello!'},
        ...     {'role': 'user', 'content': 'What did I say?'},
        ... ]
        True
        >>> [m['role'] for m in chat.messages]
        ['system', 'user', 'assistant', 'user', 'assistant']
        >>> chat.messages[-1]
        {'role': 'assistant', 'content': 'You said Hi.'}
        """
        self.messages.append({'role': 'user', 'content': message})
        reply = llm(self.messages, temperature=temperature)
        self.messages.append({'role': 'assistant', 'content': reply})
        return reply


def repl(temperature=0.8):
    """Read input, reply like a pirate, and loop until Ctrl-C or end of input.

    Two inputs produce two printed replies; end of input exits cleanly:

    >>> from unittest.mock import patch
    >>> sent = []
    >>> with patch('builtins.input', side_effect=['Ahoy', 'What did I say?', EOFError]), \\
    ...      patch.object(client.chat.completions, 'create',
    ...                   side_effect=_fake_api(['Arr, hello!', 'Ye said Ahoy.'], sent)) as create:
    ...     repl(temperature=0)
    Arr, hello!
    Ye said Ahoy.
    <BLANKLINE>

    Each input is sent to the model at the requested temperature, and the
    second request retains the first exchange:

    >>> create.call_count
    2
    >>> [call.kwargs['temperature'] for call in create.call_args_list]
    [0, 0]
    >>> sent[0][1:]
    [{'role': 'user', 'content': 'Ahoy'}]
    >>> sent[1][1:] == [
    ...     {'role': 'user', 'content': 'Ahoy'},
    ...     {'role': 'assistant', 'content': 'Arr, hello!'},
    ...     {'role': 'user', 'content': 'What did I say?'},
    ... ]
    True

    Ctrl-C exits cleanly too, even mid-conversation:

    >>> sent = []
    >>> with patch('builtins.input', side_effect=['Ahoy', KeyboardInterrupt]), \\
    ...      patch.object(client.chat.completions, 'create',
    ...                   side_effect=_fake_api(['Arr!'], sent)):
    ...     repl(temperature=0)
    Arr!
    <BLANKLINE>

    End of input before any message sends nothing:

    >>> sent = []
    >>> with patch('builtins.input', side_effect=EOFError), \\
    ...      patch.object(client.chat.completions, 'create',
    ...                   side_effect=_fake_api([], sent)):
    ...     repl(temperature=0)
    <BLANKLINE>
    >>> sent
    []
    """
    chat = Chat(system='You are a helpful assistant. You always speak like a pirate.')
    try:
        while True:
            user_input = input('chat> ')
            print(chat.send_message(user_input, temperature=temperature))
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == '__main__':
    repl()
