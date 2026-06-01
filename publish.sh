#!/bin/bash
# Read sheet → regenerate static profile shells + roster.json → deploy to Netlify.
# Pass --no-deploy to do a dry build (writes files locally without deploying).
set -e
cd "$(dirname "$0")"
exec /opt/homebrew/bin/python3 publish.py "$@"
