#!/usr/bin/env bash
set -e

cd /workspace/irs_ws
colcon build --packages-select hand_solo_virtual_nav
source install/local_setup.bash
ros2 launch hand_solo_virtual_nav mapping_launch.py
