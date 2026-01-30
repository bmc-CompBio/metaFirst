#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# start_ui_remote.sh
# Starts the metaFirst web UI for remote access.
# Usage: ./scripts/start_ui_remote.sh <HOSTNAME_OR_IP>
# -----------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
    cat <<EOF
Usage: $(basename "$0") <HOSTNAME_OR_IP>

Starts the metaFirst web UI accessible from other machines.

Arguments:
  HOSTNAME_OR_IP   The hostname or IP address clients will use to connect.
                   This is added to Vite's allowed hosts.

Examples:
  $(basename "$0") myserver.example.edu
  $(basename "$0") 192.168.1.100

The UI will be available at: http://<HOSTNAME_OR_IP>:5173
EOF
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

HOSTNAME="$1"

# Validate we have the UI directory
if [[ ! -f "$REPO_ROOT/supervisor-ui/package.json" ]]; then
    echo "ERROR: supervisor-ui/package.json not found"
    echo "Run from the repository root."
    exit 1
fi

cd "$REPO_ROOT/supervisor-ui"

# Check npm is available
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm not found. Please install Node.js 18+."
    exit 1
fi

# Install dependencies if needed
if [[ ! -d "node_modules" ]]; then
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "Starting web UI for remote access..."
echo "Allowed host: $HOSTNAME"
echo "URL: http://$HOSTNAME:5173"
echo ""

export VITE_ALLOWED_HOSTS="$HOSTNAME"
exec npm run dev -- --host 0.0.0.0 --port 5173
