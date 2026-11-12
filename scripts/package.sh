#!/usr/bin/env bash
# Builds dist/hibira-<version>.difypkg from the files Dify needs at runtime.
# -D leaves out directory entries: the plugin daemon fails to install a
# package that has them ("read provider: is a directory").
set -euo pipefail
cd "$(dirname "$0")/.."
version=$(sed -n 's/^version: *//p' manifest.yaml | head -1)
mkdir -p dist
out="dist/hibira-${version}.difypkg"
rm -f "$out"
zip -qrXD "$out" manifest.yaml main.py hibira_client.py requirements.txt README.md PRIVACY.md LICENSE \
  provider tools _assets -x '*/__pycache__/*' '*.pyc'
echo "$out"
