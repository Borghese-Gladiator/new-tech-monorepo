# Textual
Textual, a Python toolkit and framework for creating beautiful, functional text-based user interface (TUI) applications. `htop` is a basic example of a TUI.

Textual works by providing a set of widgets, layouts, and styling options, enabling you to create responsive and interactive console apps.

Resource:
- https://realpython.com/python-textual/

Notable TUIs:
- Memray - memory profiler for Python
- Toolong - view, tail, merge, and search log files
- Dolphie - real-time analytics into MySQL/MariaDB & ProxySQL
- Harlequin - database client
- https://terminal-apps.dev/
- https://github.com/rothgar/awesome-tuis?tab=readme-ov-file

## Local Setup
- `poetry install`
- `poetry run main.py`

## Implementation Steps
- `poetry init`
- update `pyproject.toml` to fix install error
  - `requires-python = ">=3.12,<4.0.0"`
- `poetry add textual`
- `poetry add textual-dev --dev`
- `Invoke-Expression (poetry env activate)`
  - Poetry 2.0.0 - new command to activate env -> changed because of [link](https://github.com/python-poetry/poetry/issues/9395?utm_source=chatgpt.com)


1. **Events** are usually triggered by a user interaction with a UI, such as a mouse click or a keystroke. They can also be associated with a timer tick or the arrival of a network packet. You’ll process events using event handlers, which are methods that do something when the event occurs.
2. **Actions** are usually triggered by a specific user action, such as a keypress or a click on a hotlink in some text. You’ll process an action with a regular method prefixed with .action_ and followed by the action’s name.
