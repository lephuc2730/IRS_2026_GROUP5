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


## Exact Lab 04 Part 6 and Lab 05 TF GUI evidence

A final verification run followed the remaining lab-sheet steps literally in the official unit environment.

### Lab 04 Part 6.1

Both Week 5 nodes were run at the same time:

- `/pineapple_gossip_bot`
- `/plc_hmi_listener`

The same run also captured:

- `ros2 node list`
- `ros2 topic info /status_updates -v`
- `ros2 interface show std_msgs/String` (with the canonical `std_msgs/msg/String` fallback)
- a live `rqt_graph` GUI screenshot
- publisher output and live PLC-listener output

Evidence files are stored under `docs/evidence/`, including:

- `lab04_nodes.txt`
- `lab04_publisher.log`
- `lab04_listener.log`
- `lab04_status_topic_info.txt`
- `lab04_rqt_graph.png`

### Lab 05 Step 9

While the mapping launch file was running, the exact command requested by the lab was launched:

```bash
ros2 run rqt_tf_tree rqt_tf_tree
```

The live GUI was captured from the official warehouse runtime. Evidence files include:

- `docs/evidence/lab05_rqt_tf_tree.png`
- `docs/evidence/lab05_rqt_tf_tree_root.png`
- `docs/evidence/lab05_rqt_tf_tree.log`
- `docs/evidence/lab05_nodes.txt`

Exact Lab 04-05 evidence run:
https://github.com/lephuc2730/IRS_2026_GROUP5/actions/runs/37431121395

## Scope

This is genuine runtime evidence from the official public course simulation running headlessly in Ubuntu CI. It is not a manually fabricated screenshot or synthetic map. The headless environment is different from an in-person lab desktop, but it uses the official warehouse Docker image and ROS2 workspace image.
