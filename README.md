# IRS_2026_GROUP5 - Industrial Robots and Systems

This repository contains the Group 5 work for **12059 Industrial Robots and Systems**, including PLC/ROS2 communication, mapping and Nav2 navigation, and MoveIt arm motion.

## Week 5 - PLC / ROS2 communication

The `pa_warehouse_status` package contains:

- `pineapple_gossip_bot`: publishes `std_msgs/String` status messages to `/status_updates`.
- `plc_hmi_listener`: subscribes to a configurable PLC/HMI status topic and parses the JSON fields required by Lab 04.
- `plc_topic_probe`: checks likely String status topics for JSON containing `stamp`, `box`, and `counts`.
- `warehouse_mission_controller`: integrates PLC status, MoveIt arm motion, Nav2 delivery, placing, and return-to-home.

Build:

```bash
cd /workspace/irs_ws
colcon build --packages-select pa_warehouse_status hand_solo_virtual_nav hand_solo_arm
source install/local_setup.bash
```

To identify the live PLC JSON topic:

```bash
ros2 run pa_warehouse_status plc_topic_probe
```

## Week 6 - Mapping and Nav2

The `hand_solo_virtual_nav` package contains:

- `launch/mapping_launch.py`
- `launch/nav_launch.py`
- `launch/nav_launch_with_waypoints.py`
- `config/pa_slam_params.yaml`
- `config/pa_nav2_params.yaml`
- `rviz/pa_rviz_mapping.rviz`
- `rviz/pa_rviz_nav2.rviz`
- `hs_waypoint_follower`

The saved warehouse map is:

```text
pa_warehouse_map_01.pgm
pa_warehouse_map_01.yaml
```

## Integrated warehouse cycle

The mission controller coordinates the system in this order:

```text
PLC box-ready status
        |
        v
MoveIt pick/retract arm motion
        |
        v
Nav2 -> drop-off
        |
        v
MoveIt place/return arm motion
        |
        v
Nav2 -> Home
        |
        v
IDLE / ready for next cycle
```

Start the controller after the simulator, MoveIt and Nav2 action servers are running:

```bash
ros2 run pa_warehouse_status warehouse_mission_controller
```

For a reliable presentation demo, start one complete cycle manually:

```bash
ros2 service call /warehouse/start_cycle std_srvs/srv/Trigger "{}"
```

Watch the mission state:

```bash
ros2 topic echo /warehouse/mission_status
```

The expected state sequence is:

```text
IDLE
PICKING
NAVIGATING_DROPOFF
PLACING
NAVIGATING_HOME
COMPLETE
IDLE
```

### Enable PLC automatic triggering

The controller listens to `/hmi/unified_status`. Automatic triggering is disabled by default so an unexpected PLC status cannot start the robot during setup.

Enable it when the live PLC `box.location` value is confirmed:

```bash
ros2 run pa_warehouse_status warehouse_mission_controller --ros-args \
  -p plc_auto_trigger:=true
```

By default, a location containing `ready`, `pickup`, `pick`, or `conveyor` can trigger the cycle. Override the accepted values if the simulator uses different text.

### Adjust drop-off and home positions

The Nav2 coordinates are ROS parameters. They currently use the tested Group 5 waypoint/map region and can be changed without editing Python:

```bash
ros2 run pa_warehouse_status warehouse_mission_controller --ros-args \
  -p delivery_x:=0.75 -p delivery_y:=0.0 -p delivery_yaw:=1.5708 \
  -p home_x:=0.15 -p home_y:=-0.15 -p home_yaw:=-1.5708
```

## Important demonstration note

The current MoveIt sequence demonstrates arm positioning for pick/retract and place/return. It does **not** implement a physical gripper/box-attachment action. During the presentation, describe it as the manipulation motion sequence unless a separate gripper/attachment mechanism is running in the simulator.

## Evidence note

Runtime screenshots and exact live PLC values depend on the running course simulation. They should be captured from the real simulator and are not fabricated in this repository.
