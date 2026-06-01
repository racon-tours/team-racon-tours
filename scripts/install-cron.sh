#!/bin/bash
# Install the nightly publish LaunchAgent on this Mac.
# Idempotent.
set -e
PLIST=~/Library/LaunchAgents/com.racon.team-publish.plist
SRC="$(cd "$(dirname "$0")/.." && pwd)/scripts/com.racon.team-publish.plist"
cp "$SRC" "$PLIST"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
echo "loaded:"
launchctl list | grep team-publish
echo
echo "next runs nightly at 3:15am. logs: ~/Library/Logs/team-publish.log"
echo "to run now: ./publish.sh"
