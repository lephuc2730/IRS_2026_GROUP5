# Runtime evidence from the official unit environment

The project was executed through GitHub Actions on an Ubuntu 24.04 runner using the public course repository and Docker images from `CollaborativeRoboticsLab/industrial-robots-and-systems-world`.

## Week 5 evidence

- `pa_warehouse_status` built successfully inside the official `omron-workspace` container.
- `pineapple_gossip_bot`, `plc_hmi_listener`, and `plc_topic_probe` were installed as ROS2 executables.
- `pineapple_gossip_bot` published successfully to `/status_updates`.
- The Robot HMI was opened in the official `IRS_Warehouse` simulation and displayed:
  - `Status Update: Group 5 ROS2 communication hub is running.`
- The live PLC/HMI status topic was confirmed as `/hmi/unified_status`.
- Its live message contained JSON with the required `stamp`, `box`, and `counts` objects.

Week 5 HMI proof run:
https://github.com/lephuc2730/IRS_2026_GROUP5/actions/runs/37424515300

## Week 6 evidence

The official simulation published:

- `/virtual_hand_solo/scan`
- `/virtual_hand_solo/odom`
- `/tf`
- `/tf_static`
- `/cmd_vel`

The live LaserScan reported frame:
`virtual_hand_solo/lidar_link`

The live TF graph during mapping showed:

```text
map
  -> virtual_hand_solo/odom
      -> virtual_hand_solo/base_link
          -> camera_link
          -> virtual_hand_solo/lidar_link
```

The project launched SLAM Toolbox and RViz, published real velocity commands to `/cmd_vel`, produced a live `/map` occupancy grid, and saved:

- `pa_warehouse_map_01.pgm`
- `pa_warehouse_map_01.yaml`

The save-map service returned `result=0`, and the runtime log reported `Map saved successfully`.

Week 5-6 runtime evidence run:
https://github.com/lephuc2730/IRS_2026_GROUP5/actions/runs/37423519986

## Scope

This is genuine runtime evidence from the official public course simulation running headlessly in Ubuntu CI. It is not a manually fabricated screenshot or synthetic map. The headless environment is different from an in-person lab desktop, but it uses the official warehouse Docker image and ROS2 workspace image.
