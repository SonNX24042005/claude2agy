#!/usr/bin/env bash
# Quick runner for Claude2AGY without requiring global pip installation

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHONPATH="$SCRIPT_DIR" python3 -m claude2agy.cli "$@"
