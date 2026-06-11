#!/usr/bin/env bash
# Setup optional global exchange CSV files for universe_extension.py
# Download exchange listings and set env vars in IBBack/.env

set -euo pipefail

DATA_DIR="${1:-./IBBack/data/exchanges}"
mkdir -p "$DATA_DIR"

echo "Global exchange CSV setup"
echo "========================="
echo ""
echo "Place CSV files with Symbol,Name columns in: $DATA_DIR"
echo ""
echo "Then add to IBBack/.env:"
echo "  TSX_LIST_CSV=$DATA_DIR/tsx.csv"
echo "  LSE_LIST_CSV=$DATA_DIR/lse.csv"
echo "  ASX_LIST_CSV=$DATA_DIR/asx.csv"
echo "  HK_LIST_CSV=$DATA_DIR/hk.csv"
echo "  JP_LIST_CSV=$DATA_DIR/jp.csv"
echo ""
echo "US listings (NASDAQ/NYSE/AMEX) are fetched automatically."
echo "Curated global tickers and pytickersymbols indices are loaded when available."
echo ""
echo "Install optional dependency:"
echo "  pip install pytickersymbols"
