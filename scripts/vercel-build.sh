#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/IBFRONT"

npm ci
npm run build

rm -rf "$ROOT/public"
mkdir -p "$ROOT/public"
cp -r dist/* "$ROOT/public/"

echo "Vercel build: copied IBFRONT/dist -> public/"
