#!/usr/bin/env bash
set -euo pipefail

WEB_UI_URL=${WEB_UI_URL:-http://localhost:3000}
HMI_URL=${HMI_URL:-http://localhost:8080}
RELAY_URL=${RELAY_URL:-http://localhost:8082}
BREAKER_URL=${BREAKER_URL:-http://localhost:8081}

say() { echo -e "[E2E] $*"; }

req() { curl -fsS "$@"; }

say "Running orchestrated test via web-interface /api/run-tests"

# Kick HMI/IEDs to refresh status first (non-fatal)
curl -fsS -X POST "$WEB_UI_URL/api/refresh-status" >/dev/null || true

JSON=$(curl -fsS -X POST "$WEB_UI_URL/api/run-tests" || true)

# Pretty print summary using python3 if available, else raw JSON
if command -v python3 >/dev/null 2>&1; then
TMP_JSON=$(mktemp)
printf '%s' "$JSON" > "$TMP_JSON"
python3 - "$TMP_JSON" "$HMI_URL" "$RELAY_URL" "$BREAKER_URL" <<'PY'
import sys, json, urllib.request
path = sys.argv[1]
try:
    with open(path, 'r') as f:
        data = f.read().strip()
except Exception:
    data = ''
if not data:
    print("No JSON received from web-interface /api/run-tests")
    sys.exit(1)
doc = json.loads(data)
ok = doc.get('ok')
print("Summary: {} ({} ms)".format('PASS' if ok else 'FAIL', doc.get('durationMs', '?')))
for r in doc.get('results', []):
    print(" - {:28} : {} ({} ms)".format(r.get('name','?'), 'OK' if r.get('ok') else 'FAIL', r.get('elapsed', '?')))

# Live state snapshots
def grab(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {}

hmi = grab(sys.argv[1] + "/data")
relay = grab(sys.argv[2])
brk = grab(sys.argv[3])

print("\nLive state:")
print(" - Relay tripCommand   : {}".format(relay.get('tripCommand')))
print(" - Relay breakerStatus : {} (feedback)".format(relay.get('breakerStatus')))
print(" - Breaker tripReceived: {}".format(brk.get('tripReceived')))
print(" - Breaker position    : {} / breakerOpen:".format(brk.get('position', 'UNKNOWN')), brk.get('breakerOpen'))
print(" - HMI   breakerStatus : {}".format(hmi.get('breakerStatus')))

# Exit non-zero on failure
sys.exit(0 if ok else 1)
PY
rm -f "$TMP_JSON"
else
  if [ -n "$JSON" ]; then
    echo "$JSON"
  else
    echo "No response from $WEB_UI_URL/api/run-tests" >&2
    exit 1
  fi
fi

say "Done."
