# Week 5 / Week 6 Evidence

This folder contains the runtime evidence collected from the official Pine-Apple ROS2 Jazzy environment.

## Week 5 files

- **lab04_rqt_graph.png** — original live rqt_graph screenshot.
- **lab04_rqt_graph_CLEAR.svg** — enlarged, readable version of the verified Week 5 graph for use in the portfolio.
- **lab04_nodes.txt** — live `ros2 node list` output.
- **lab04_status_topic_info.txt** — live `ros2 topic info /status_updates -v` output.
- **lab04_status_updates_sample.txt** — live message captured from `/status_updates`.
- **lab04_plc_sample.txt** — live PLC/HMI JSON sample from `/hmi/unified_status`.
- **lab04_publisher.log** and **lab04_listener.log** — simultaneous publisher/subscriber runtime logs.

## Week 6 files

- **lab05_rqt_tf_tree.png** — original live rqt_tf_tree screenshot captured while mapping.
- **lab05_nodes.txt** — nodes active during Week 6 mapping.
- **lab05_tf_echo.txt** — live TF evidence.

## Main project code

Week 5 package:

`pa_warehouse_status/pa_warehouse_status/`

Week 6 package:

`hand_solo_virtual_nav/`

## Git history

On the repository home page, click **Commits** above the file list to view the commit history. A key Week 5 commit is:

`effb88a — Week 5: Implemented ROS2 publisher-subscriber communication nodes`
