(ty ChatGPT for explaining this)

# python-registry-first
A lightweight plugin framework demo in Python using the **registry pattern**.  
Includes example image plugins (resize/compress/watermark), a CLI runner, and a JSON REST API server.

This repository demonstrates:
- automatic plugin discovery & registration (metaclass)
- plugin metadata and enable/disable via `config.yaml`
- CLI runner (`runner.py`)
- REST API server (`server.py`) built with FastAPI for programmatic usage
- tests (pytest) and optional real image processing (Pillow)

## Project layout
```
plugin_demo/
├─ plugins/
│  ├─ **init**.py
│  ├─ resize.py
│  ├─ compress.py
│  └─ watermark.py
├─ plugin_base.py
├─ runner.py
├─ config.yaml
├─ requirements.txt
└─ tests/
  └─ test_plugins.py
```

## Local Setup
```
// setup local
poetry install
Invoke-Expression (poetry env activate)

// run script
python .\runner.py list
python runner.py run resize <img_path> 800 800
```
