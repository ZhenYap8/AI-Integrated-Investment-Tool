#!/usr/bin/env bash
set -euo pipefail

# test-proscons.sh — Snapshot and compare pros/cons between two API endpoints.
# Usage:
#   bash scripts/test-proscons.sh \
#     --url1 http://127.0.0.1:8000/api/analyze \
#     --url2 http://127.0.0.1:8001/api/analyze \
#     --query AAPL --years 3 [--seed 1234] [--debug]
# Optional thresholds (kept constant across runs unless overridden):
#   --rev_cagr_min 0.05 --op_margin_min 0.10 --nd_eq_max 1.0 --interest_cover_min 4.0 --roe_min 0.10

command -v jq >/dev/null 2>&1 || { echo "This script requires 'jq'. Install via: brew install jq" >&2; exit 1; }

# Defaults
URL1="http://127.0.0.1:8000/api/analyze"
URL2=""
QUERY="AAPL"
YEARS="3"
SEED="1234"
DEBUG_FLAG="false"
TEMP=0
TOPP=1
REV_CAGR_MIN="0.05"
OP_MARGIN_MIN="0.10"
ND_EQ_MAX="1.0"
INTEREST_COVER_MIN="4.0"
ROE_MIN="0.10"

urlencode() {
  # Minimal urlencode for query params
  local LANG=C
  local s="$1"
  local i c e=""
  for (( i=0; i<${#s}; i++ )); do
    c=${s:$i:1}
    case "$c" in
      [a-zA-Z0-9.~_-]) e+="$c" ;;
      *) printf -v e '%s%%%02X' "$e" "'"$c"'" ;;  # shellcheck disable=SC2059
    esac
  done
  printf '%s' "$e"
}

usage() {
  grep '^# ' "$0" | sed 's/^# //'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url1) URL1="$2"; shift 2 ;;
    --url2) URL2="$2"; shift 2 ;;
    --query) QUERY="$2"; shift 2 ;;
    --years) YEARS="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --debug) DEBUG_FLAG="true"; shift 1 ;;
    --rev_cagr_min) REV_CAGR_MIN="$2"; shift 2 ;;
    --op_margin_min) OP_MARGIN_MIN="$2"; shift 2 ;;
    --nd_eq_max) ND_EQ_MAX="$2"; shift 2 ;;
    --interest_cover_min) INTEREST_COVER_MIN="$2"; shift 2 ;;
    --roe_min) ROE_MIN="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

[[ -n "$URL2" ]] || URL2="$URL1"

QS="query=$(urlencode "$QUERY")&years=$(urlencode "$YEARS")&seed=$(urlencode "$SEED")&temperature=$TEMP&top_p=$TOPP\
&rev_cagr_min=$REV_CAGR_MIN&op_margin_min=$OP_MARGIN_MIN&nd_eq_max=$ND_EQ_MAX&interest_cover_min=$INTEREST_COVER_MIN&roe_min=$ROE_MIN"
if [[ "$DEBUG_FLAG" == "true" ]]; then QS+="&debug=true"; fi

OUTDIR=$(mktemp -d 2>/dev/null || mktemp -d -t proscons)
OUT1="$OUTDIR/out1.json"
OUT2="$OUTDIR/out2.json"

fetch() {
  local url="$1"; local out="$2"
  echo "Fetching: $url?$QS" >&2
  curl -sS "$url?$QS" -H 'Accept: application/json' -o "$out"
}

fetch "$URL1" "$OUT1"
fetch "$URL2" "$OUT2"

# Validate JSON
for f in "$OUT1" "$OUT2"; do
  if ! jq -e .<"$f" >/dev/null 2>&1; then
    echo "Invalid JSON in $f" >&2
    exit 2
  fi
done

# Extract and normalize pros/cons
P1="$OUTDIR/p1.txt"; P2="$OUTDIR/p2.txt"
PS1="$OUTDIR/ps1.txt"; PS2="$OUTDIR/ps2.txt"

jq -r '.pros[]?, .cons[]?' "$OUT1" | sed 's/^\s\+//;s/\s\+$//' | LC_ALL=C sort -u > "$P1"
jq -r '.pros[]?, .cons[]?' "$OUT2" | sed 's/^\s\+//;s/\s\+$//' | LC_ALL=C sort -u > "$P2"

# Counts
PROS1=$(jq '.pros|length // 0' "$OUT1"); CONS1=$(jq '.cons|length // 0' "$OUT1"); FIND1=$(jq '.findings|length // 0' "$OUT1")
PROS2=$(jq '.pros|length // 0' "$OUT2"); CONS2=$(jq '.cons|length // 0' "$OUT2"); FIND2=$(jq '.findings|length // 0' "$OUT2")

# LLM/OpenAI diagnostics
FROMAI1=$(jq -r '.fromAI // .meta.fromAI // false' "$OUT1")
FROMAI2=$(jq -r '.fromAI // .meta.fromAI // false' "$OUT2")
LLM1=$(jq -r '(.debug.llm_provider // .meta.llm_provider // "n/a")' "$OUT1")
LLM2=$(jq -r '(.debug.llm_provider // .meta.llm_provider // "n/a")' "$OUT2")
CALLED1=$(jq -r '(.debug.llm_called // .meta.llm_called // false)' "$OUT1")
CALLED2=$(jq -r '(.debug.llm_called // .meta.llm_called // false)' "$OUT2")
OA_REQ1=$(jq -r '(.debug.openai.request_id // .meta.openai_request_id // "")' "$OUT1")
OA_REQ2=$(jq -r '(.debug.openai.request_id // .meta.openai_request_id // "")' "$OUT2")
EVURLS1=$(jq '[.findings[]?.evidence[]? | select(.url!=null)] | length' "$OUT1")
EVURLS2=$(jq '[.findings[]?.evidence[]? | select(.url!=null)] | length' "$OUT2")

LIKELY1="no"; if [[ "$FROMAI1" == "true" || "$LLM1" != "n/a" || "$CALLED1" == "true" || -n "$OA_REQ1" ]]; then LIKELY1="yes"; fi
LIKELY2="no"; if [[ "$FROMAI2" == "true" || "$LLM2" != "n/a" || "$CALLED2" == "true" || -n "$OA_REQ2" ]]; then LIKELY2="yes"; fi

echo "=== Summary ==="
echo "URL1: $URL1"
echo "  pros=$PROS1 cons=$CONS1 findings=$FIND1 fromAI=$FROMAI1 llm_provider=$LLM1 llm_called=$CALLED1 ev_urls=$EVURLS1 openai_req_id=${OA_REQ1:-} (openai_called_likely=$LIKELY1)"
echo "URL2: $URL2"
echo "  pros=$PROS2 cons=$CONS2 findings=$FIND2 fromAI=$FROMAI2 llm_provider=$LLM2 llm_called=$CALLED2 ev_urls=$EVURLS2 openai_req_id=${OA_REQ2:-} (openai_called_likely=$LIKELY2)"

# Jaccard overlap of combined pros+cons
UCOUNT=$(cat "$P1" "$P2" | LC_ALL=C sort -u | wc -l | tr -d ' ')
ICOUNT=$(comm -12 "$P1" "$P2" | wc -l | tr -d ' ')
if [[ "$UCOUNT" -eq 0 ]]; then JACCARD="0.000"; else JACCARD=$(awk -v i="$ICOUNT" -v u="$UCOUNT" 'BEGIN { printf "%.3f", (u==0?0:i/u) }'); fi

echo "Overlap (Jaccard) pros+cons: $JACCARD (|∩|=$ICOUNT, |∪|=$UCOUNT)"

# Unified diff of pros+cons
echo "\n=== Diff (pros+cons) ==="
if ! diff -u "$P1" "$P2"; then echo "(differences above)"; else echo "(no differences)"; fi

# Hash of selection for quick regression checks
hasher() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256; elif command -v sha256sum >/dev/null 2>&1; then sha256sum; else openssl dgst -sha256 | awk '{print $2}'; fi
}

H1=$(jq -r '.findings[]? | [.item, .direction, (.primary_url // "")] | @tsv' "$OUT1" | hasher | awk '{print $1}')
H2=$(jq -r '.findings[]? | [.item, .direction, (.primary_url // "")] | @tsv' "$OUT2" | hasher | awk '{print $1}')

echo "\nSelection hash:" \
     "\n  URL1: $H1" \
     "\n  URL2: $H2"

# Per-URL histograms to check per_url cap behavior
echo "\n=== primary_url histogram (URL1) ==="
jq -r '.findings[]?.primary_url // empty' "$OUT1" | LC_ALL=C sort | uniq -c | LC_ALL=C sort -nr | head -20

echo "\n=== primary_url histogram (URL2) ==="
jq -r '.findings[]?.primary_url // empty' "$OUT2" | LC_ALL=C sort | uniq -c | LC_ALL=C sort -nr | head -20

# Optional: Show detailed diagnostics if debug=true
if [[ "$DEBUG_FLAG" == "true" ]]; then
  echo "\n=== diagnostics (URL1) ==="
  if jq -e 'has("findings") and .findings != null and (.findings|type=="array") and (.findings|length>0)' "$OUT1" >/dev/null; then
    echo "-- top findings --"
    jq -r '.findings[] | [.direction, (.score // .weight // 0), (.primary_url // .evidence[0].url // "-"), .item] | @tsv' "$OUT1" | head -20
  else
    echo "-- pros (top) --"
    jq -r '.pros[]? | @text' "$OUT1" | head -10
    echo "-- cons (top) --"
    jq -r '.cons[]? | @text' "$OUT1" | head -10
  fi

  echo "\n=== diagnostics (URL2) ==="
  if jq -e 'has("findings") and .findings != null and (.findings|type=="array") and (.findings|length>0)' "$OUT2" >/dev/null; then
    echo "-- top findings --"
    jq -r '.findings[] | [.direction, (.score // .weight // 0), (.primary_url // .evidence[0].url // "-"), .item] | @tsv' "$OUT2" | head -20
  else
    echo "-- pros (top) --"
    jq -r '.pros[]? | @text' "$OUT2" | head -10
    echo "-- cons (top) --"
    jq -r '.cons[]? | @text' "$OUT2" | head -10
  fi
fi

echo "\nArtifacts in: $OUTDIR"
