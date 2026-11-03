#!/usr/bin/env bash
set -euo pipefail

# Run this on the Ubuntu host from the folder that contains compose.yaml.
# It waits for the Grand Challenge controller to publish
# BOX_RELEASED_ON_SHELF, raises the Pine-Apple simulator window, and captures
# the desktop/window as placement evidence.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUT_DIR="${1:-$REPO_ROOT/docs/evidence/grand_challenge}"
mkdir -p "$OUT_DIR"

WS_ID="$(docker compose ps -q omron-workspace)"
if [ -z "$WS_ID" ]; then
  echo "[ERROR] omron-workspace is not running."
  exit 1
fi

echo "[WAIT] Waiting for BOX_RELEASED_ON_SHELF..."
docker exec "$WS_ID" bash -lc '
  source /opt/ros/jazzy/setup.bash
  if [ -f /workspace/irs_ws/install/setup.bash ]; then
    source /workspace/irs_ws/install/setup.bash
  fi
  ros2 topic echo /warehouse/mission_status std_msgs/msg/String
' | grep -m1 'BOX_RELEASED_ON_SHELF' >/dev/null

echo "[OK] Box release detected."

if command -v xdotool >/dev/null 2>&1; then
  SIM_ID="$(xdotool search --onlyvisible --name 'IRS_Warehouse' 2>/dev/null | head -1 || true)"
  if [ -z "$SIM_ID" ]; then
    SIM_ID="$(xdotool search --onlyvisible --name 'Warehouse' 2>/dev/null | head -1 || true)"
  fi
  if [ -n "$SIM_ID" ]; then
    xdotool windowactivate --sync "$SIM_ID" || true
    xdotool windowraise "$SIM_ID" || true
    sleep 1
  fi
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$OUT_DIR/box_on_shelf_$STAMP.png"

if command -v gnome-screenshot >/dev/null 2>&1; then
  gnome-screenshot -f "$OUT"
elif command -v import >/dev/null 2>&1; then
  import -window root "$OUT"
elif command -v scrot >/dev/null 2>&1; then
  scrot "$OUT"
else
  echo "[ERROR] No screenshot tool found."
  echo "Install one of: gnome-screenshot, imagemagick, or scrot."
  exit 2
fi

echo "[SAVED] $OUT"
