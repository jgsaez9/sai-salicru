#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bootstrap="$HOME/.cache/salicru-bootstrap"
venv="$HOME/.cache/salicru-tests"
if [ ! -x "$bootstrap/bin/uv" ]; then
    python3 -m venv "$bootstrap"
    "$bootstrap/bin/pip" install uv
fi
if [ ! -x "$venv/bin/python" ]; then
    "$bootstrap/bin/uv" venv --python 3.14 "$venv"
fi
"$bootstrap/bin/uv" pip install --python "$venv/bin/python" -r requirements-test.txt
"$venv/bin/python" -c 'import importlib.metadata as m; print("HA", m.version("homeassistant")); print("Test plugin", m.version("pytest-homeassistant-custom-component"))'
"$venv/bin/ruff" check --fix custom_components tests
"$venv/bin/ruff" format custom_components tests
"$venv/bin/pytest" -q
