"""compact tool: replace a long chat history with a short summary."""


def compact(chat):
    """
    Summarize chat's conversation in at most five lines and replace
    chat.messages with a single entry holding that summary.

    >>> from chat import Chat, _FakeClient
    >>> sent = []
    >>> summary = 'User greeted.\\nAssistant replied.\\nl3\\nl4\\nl5\\nl6 dropped'
    >>> chat = Chat(system='Be brief.', client=_FakeClient([summary], sent))
    >>> chat.messages += [{'role': 'user', 'content': 'Hi'},
    ...                   {'role': 'assistant', 'content': 'Hello!'}]
    >>> print(compact(chat))
    User greeted.
    Assistant replied.
    l3
    l4
    l5
    >>> chat.messages
    [{'role': 'user', 'content': 'User greeted.\nAssistant replied.\nl3\nl4\nl5'}]
    >>> sent[0][-1]['role']
    'user'
    """
    from chat import MODEL
    request = chat.messages + [{
        'role': 'user',
        'content': 'Summarize this conversation in at most five short lines.',
    }]
    completion = chat.client.chat.completions.create(
        messages=request, model=MODEL, timeout=30)
    text = completion.choices[0].message.content or ''
    lines = [line for line in text.splitlines() if line.strip()][:5]
    summary = '\n'.join(lines)
    chat.messages = [{'role': 'user', 'content': summary}]
    return summary
