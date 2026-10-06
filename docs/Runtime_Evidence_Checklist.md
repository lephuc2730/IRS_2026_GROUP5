# Runtime evidence still required

These items require the University ROS2/Docker simulation or another compatible ROS2 Jazzy environment. They cannot be truthfully generated from static files alone.

## Week 5

1. Robot HMI showing messages from `/status_updates`.
2. `ros2 topic echo` output proving the exact PLC status topic and showing JSON with `stamp`, `box`, and `counts`.
3. Optional final `rqt_graph` screenshot while both Week 5 nodes are running.

## Week 6

1. `rqt_tf_tree` screenshot while mapping is running.
2. RViz2 screenshot showing the occupancy grid being created.
3. Saved `pa_warehouse_map_01.pgm` and `pa_warehouse_map_01.yaml`.

## Commands

```bash
# Week 5
ros2 topic list
ros2 run pa_warehouse_status pineapple_gossip_bot
ros2 run pa_warehouse_status plc_topic_probe
ros2 run rqt_graph rqt_graph

# Week 6
ros2 run rqt_tf_tree rqt_tf_tree
ros2 launch hand_solo_virtual_nav mapping_launch.py
```
