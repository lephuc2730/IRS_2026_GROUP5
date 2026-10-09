# Week 7 / Lab 06 — Autonomous Navigation Runtime Evidence

This Week 7 project was tested in the official Pine-Apple warehouse environment from the public course repository `CollaborativeRoboticsLab/industrial-robots-and-systems-world` using ROS2 Jazzy.

## Lecture concepts applied

The implementation follows the Week 6 localisation foundation and Week 7 navigation architecture:

- AMCL provides particle-filter localisation on the saved warehouse map.
- REP-105 frame relationships use `map -> virtual_hand_solo/odom -> virtual_hand_solo/base_link`.
- Nav2 separates global planning from local real-time control.
- The Planner Server uses `nav2_navfn_planner::NavfnPlanner` with `use_astar: false`, so the configured global search is NavFn/Dijkstra.
- The Controller Server uses `dwb_core::DWBLocalPlanner`, corresponding to the Dynamic Window / trajectory-sampling approach discussed in Lecture 07.
- Global and local costmaps use obstacle and inflation layers for safe path planning.
- The BT Navigator coordinates planning, control and recovery behavior.
- The Velocity Smoother limits acceleration/deceleration before commands reach `/cmd_vel`.

## Lab 06 Part 1 — Autonomous Navigation

The package now contains:

- `launch/nav_launch.py`
- `config/pa_nav2_params.yaml`
- `rviz/pa_rviz_nav2.rviz`
- `map/pa_warehouse_map_01.pgm`
- `map/pa_warehouse_map_01.yaml`

The Nav2 parameter file is configured for the live Hand Solo interfaces:

```text
LIDAR:      /virtual_hand_solo/scan
Odometry:   /virtual_hand_solo/odom
Base frame: virtual_hand_solo/base_link
Odom frame: virtual_hand_solo/odom
Map frame:  map
```

The Robot HMI was opened and **Autonomous Mode** was enabled before navigation.

The following lifecycle components were all verified as `active [3]`:

- map_server
- amcl
- controller_server
- planner_server
- behavior_server
- bt_navigator
- waypoint_follower
- velocity_smoother

A standalone `NavigateToPose` goal was accepted and finished with:

```text
Goal finished with status: SUCCEEDED
error_code: 0
```

## Lab 06 Part 2 — Custom Waypoint Mission

The supplied `hs_waypoint_follower.py` was completed with four waypoints and a 3-second delay between goals:

```text
Waypoint 1: (0.10, -0.50, 0.0)
Waypoint 2: (0.75,  0.00, pi/2)
Waypoint 3: (0.00,  0.60, pi)
Home:       (0.15, -0.15, -pi/2)
```

The final runtime produced:

```text
Sending Waypoint 1 (1/4)
Goal reached successfully!
Waiting 3 seconds before the next waypoint...

Sending Waypoint 2 (2/4)
Goal reached successfully!
Waiting 3 seconds before the next waypoint...

Sending Waypoint 3 (3/4)
Goal reached successfully!
Waiting 3 seconds before the next waypoint...

Sending Home (4/4)
Goal reached successfully!
Navigation sequence complete. Shutting down.
```

This verifies the custom `NavigateToPose` ActionClient, feedback handling, sequential goals, quaternion orientation conversion and Python `time.sleep()` delays.

## Portfolio-relevant configuration

AMCL initial-pose configuration:

```yaml
set_initial_pose: True
initial_pose: [0.0, 0.0, 0.0, 0.0]
```

Costmap inflation configuration:

```yaml
# local costmap
cost_scaling_factor: 3.0
inflation_radius: 1.0

# global costmap
cost_scaling_factor: 3.0
inflation_radius: 0.8
```

Saved map resolution:

```yaml
resolution: 0.050
```

Therefore each occupancy-grid cell represents **0.05 m (5 cm)**.

## Runtime proof

Final successful GitHub Actions run:

https://github.com/lephuc2730/IRS_2026_GROUP5/actions/runs/37935082673

The run used the official unit warehouse containers and captured the HMI, Nav2 lifecycle state, map/AMCL data, standalone navigation goal, custom waypoint mission and RViz navigation evidence.
