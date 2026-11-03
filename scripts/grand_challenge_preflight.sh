#!/usr/bin/env bash
set -u

echo "=== Pine-Apple Grand Challenge preflight ==="

ok=0
warn=0

check_topic() {
  local topic="$1"
  if ros2 topic list 2>/dev/null | grep -Fxq "$topic"; then
    echo "[OK] topic $topic"
  else
    echo "[MISSING] topic $topic"
    warn=$((warn + 1))
  fi
}

check_action() {
  local action="$1"
  if ros2 action list 2>/dev/null | grep -Fxq "$action"; then
    echo "[OK] action $action"
  else
    echo "[MISSING] action $action"
    warn=$((warn + 1))
  fi
}

check_node() {
  local node="$1"
  if ros2 node list 2>/dev/null | grep -Fxq "$node"; then
    echo "[OK] node $node"
  else
    echo "[MISSING] node $node"
    warn=$((warn + 1))
  fi
}

check_topic /hmi/unified_status
check_topic /virtual_hand_solo/scan
check_topic /amcl_pose
check_action /move_action
check_action /navigate_to_pose
check_node /amcl
check_node /move_group

echo
echo "--- Dynamic obstacle path ---"
if ros2 topic list 2>/dev/null | grep -Fxq /virtual_hand_solo/scan; then
  ros2 topic info /virtual_hand_solo/scan 2>/dev/null | head -n 5 || true
fi

echo
echo "--- Possible simulator grasp hook ---"
if ros2 topic list 2>/dev/null | grep -Fxq /virtual_hand_solo/han_shot_first; then
  echo "[FOUND] /virtual_hand_solo/han_shot_first"
  ros2 topic info /virtual_hand_solo/han_shot_first -v 2>/dev/null || true
else
  echo "[INFO] /virtual_hand_solo/han_shot_first not present in this run."
fi

echo
echo "--- Warehouse controller (if already running) ---"
ros2 service list 2>/dev/null | grep '^/warehouse/' || true
ros2 topic list 2>/dev/null | grep '^/warehouse/' || true

echo
if [ "$warn" -eq 0 ]; then
  echo "PRE-FLIGHT: core PLC + Nav2 + MoveIt interfaces are visible."
  exit 0
fi

echo "PRE-FLIGHT: $warn core interface(s) missing. Start the full simulator/Hand Solo stack and run this again."
exit 1
