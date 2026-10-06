# IRS_2026_GROUP5 - Weeks 5 and 6

This repository contains the project work for **12059 Industrial Robots and Systems** covering:

- **Week 5 / Lab 04:** Pine-Apple ROS2 Communication Hub
- **Week 6 / Lab 05:** Hand Solo's Mapping Mission

## Repository structure

```text
IRS_2026_GROUP5/
├── pa_warehouse_status/       # Week 5 ROS2 publisher/subscriber package
├── hand_solo_virtual_nav/     # Week 6 SLAM/RViz package
├── docs/                      # Portfolio answers and evidence guidance
├── scripts/                   # Build/run helper commands
├── VALIDATION_REPORT.md
└── README.md
```

## Week 5

The `pa_warehouse_status` package contains:

- `pineapple_gossip_bot`: publishes `std_msgs/String` status messages to `/status_updates` every 2 seconds.
- `plc_hmi_listener`: subscribes to a configurable PLC/HMI status topic and parses the JSON fields required by Lab 04.
- `plc_topic_probe`: checks likely String status topics for JSON containing `stamp`, `box`, and `counts`.

Build and run:

```bash
cd /workspace/irs_ws
colcon build --packages-select pa_warehouse_status
source install/local_setup.bash
ros2 run pa_warehouse_status pineapple_gossip_bot
```

To identify the live PLC JSON topic:

```bash
ros2 run pa_warehouse_status plc_topic_probe
```

## Week 6

The `hand_solo_virtual_nav` package contains:

- `launch/mapping_launch.py`
- `config/pa_slam_params.yaml`
- `rviz/pa_rviz_mapping.rviz`
- starter node `hs_waypoint_follower`

Build and launch:

```bash
cd /workspace/irs_ws
colcon build --packages-select hand_solo_virtual_nav
source install/local_setup.bash
ros2 launch hand_solo_virtual_nav mapping_launch.py
```

The final map must be generated during a real mapping run and saved as:

```text
pa_warehouse_map_01.pgm
pa_warehouse_map_01.yaml
```

## Evidence note

The source code, package structure and portfolio text can be prepared without Ubuntu. The Robot HMI screenshot, exact live PLC JSON confirmation, final TF-tree screenshot, RViz mapping screenshot and generated SLAM map require the running course simulation, so they are not fabricated in this repository.
