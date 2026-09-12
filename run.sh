#!/usr/bin/env sh
# EMBERLIGHT launcher (Linux / macOS).
# Usage: ./run.sh [--demo | --version | ...]
cd "$(dirname "$0")" || exit 1
exec python3 -m emberlight "$@"
