# docchat

A command-line pirate chatbot that keeps the full conversation history, so follow-up questions use earlier context. It calls a Groq-hosted model.

## Install

```
python -m pip install .
```

Put your key in a `.env` file in the folder you run from:

```
GROQ_API_KEY=your_key_here
```

## Use

```
$ chat
chat> who are you?
chat> what did I just ask you?
```

Exit with Ctrl+C or end-of-input (Ctrl+D on macOS/Linux, Ctrl+Z then Enter on Windows).

## Test

```
python -m coverage run --include="./chat.py" -m pytest chat.py --doctest-modules
python -m coverage report -m chat.py
```

Tests are offline: they patch the API client, so no real key is needed (`GROQ_API_KEY=offline-test` works).
