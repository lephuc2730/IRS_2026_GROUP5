# Lab 04 and Lab 05 Completion Checklist

This checklist maps the supplied lab sheets to the final repository and runtime evidence.

Status meanings:

- **DONE** - performed and verified in the official Pine-Apple/ROS2 environment.
- **EQUIVALENT** - the required technical outcome was performed, but a headless Ubuntu CI equivalent was used instead of the exact local GUI/manual action.

## Lab 04 - Pine-Apple ROS2 Communication Hub

### Part 1 - Explore the ROS2 ecosystem

| Lab item | Status | Evidence / note |
|---|---|---|
| Enter/update the world repository | EQUIVALENT | A fresh clone of the current official unit repository was used rather than an interactive `git pull`. |
| Start warehouse with Docker Compose | DONE | Official `irs-simulation`, `omron-workspace`, and OpenPLC runtime containers started successfully. |
| Close OpenPLC editor | EQUIVALENT | No desktop OpenPLC editor was launched in CI; the runtime container remained available for PLC status. |
| Drive/explore warehouse | EQUIVALENT | Hand Solo was driven with real ROS2 `/cmd_vel` commands rather than keyboard WASD input. |
| Open Robot HMI with R | DONE | The HMI was opened in the official `IRS_Warehouse` GUI and captured. |
| Observe status display | DONE | HMI displayed `Group 5 ROS2 communication hub is running.` |
| Open code-server at localhost:8080 | EQUIVALENT | Files were edited/built directly inside the mounted official ROS2 workspace; browser code-server was unnecessary in CI. |
| `ros2 topic list` | DONE | Live topic list captured. |
| `ros2 topic echo` interesting topics | DONE | Live scan, odometry, status-update, and PLC/HMI streams were inspected. |
| Find sensor topic | DONE | `/virtual_hand_solo/scan`. |
| Find movement/velocity topic | DONE | `/cmd_vel` and related velocity topics identified. |
| Find PLC status topic | DONE | Confirmed as `/hmi/unified_status`. |

### Part 2 - GitHub repository

| Lab item | Status | Evidence / note |
|---|---|---|
| Create Group 5 repository | DONE | `lephuc2730/IRS_2026_GROUP5`. |
| Clone/use repository in ROS2 workspace | DONE | Staged under `/workspace/irs_ws/src/IRS_2026_GROUP5` in official runtime. |
| Initial structure commit | DONE | Repository contains structured Week 5/6 commit history. |
| Push to GitHub | DONE | Main branch contains package code, maps, reports and evidence. |

### Part 3 - First ROS2 package

| Lab item | Status | Evidence / note |
|---|---|---|
| Create `pa_warehouse_status` ament_python package | DONE | Valid ROS2 Python package exists and builds in the official workspace. |
| Starter node `pineapple_gossip_bot` | DONE | Registered ROS2 executable. |
| Build with colcon | DONE | Exact build log stored in `docs/evidence/exact_build.log`. |
| Source workspace | DONE | `install/setup.bash` sourced in runtime. |
| Run node | DONE | Final implemented node runs successfully. The original one-line starter output was superseded by the completed publisher implementation. |

### Part 4 - Status update publisher

| Lab item | Status | Evidence / note |
|---|---|---|
| Publish on `status_updates` | DONE | Publisher verified. |
| Publish every 2 seconds | DONE | Live publisher log verifies repeated two-second messages. |
| Creative status messages | DONE | Multiple Group 5/Hand Solo warehouse messages implemented. |
| Rebuild/run | DONE | Verified in official workspace. |
| Robot HMI displays messages | DONE | Real HMI screenshot captured. |
| `ros2 topic echo /status_updates` | DONE | Sample stored in `docs/evidence/lab04_status_updates_sample.txt`. |

### Part 5 - PLC status listener

| Lab item | Status | Evidence / note |
|---|---|---|
| Find PLC communication topic | DONE | `/hmi/unified_status`. |
| Create `plc_hmi_listener` | DONE | Node installed and executable. |
| Subscribe to PLC topic | DONE | Live messages received. |
| Add setup.py console entry | DONE | Verified by `ros2 pkg executables`. |
| Parse JSON | DONE | `stamp`, `box`, and `counts` parsed. |
| Rebuild/run listener | DONE | Live listener log stored in `docs/evidence/lab04_listener.log`. |

### Part 6 - Testing and integration

| Lab item | Status | Evidence / note |
|---|---|---|
| Run publisher and listener simultaneously | DONE | Exact final run shows both `/pineapple_gossip_bot` and `/plc_hmi_listener` active at the same time. |
| `ros2 node list` | DONE | `docs/evidence/lab04_nodes.txt`. |
| `ros2 topic info /status_updates` | DONE | `docs/evidence/lab04_status_topic_info.txt`. |
| `ros2 interface show std_msgs/String` | DONE | Executed with canonical ROS2 message-name fallback where required; result stored in evidence. |
| Final ROS graph | DONE | Real rqt_graph capture stored in `docs/evidence/lab04_rqt_graph.png`. |
| Commit and push | DONE | Evidence and final project committed to main. |

---

## Lab 05 - Hand Solo's Mapping Mission

| Step | Status | Evidence / note |
|---|---|---|
| 1. Pull latest simulation image | DONE | Official Docker images pulled during runtime runs. |
| 2. Disable hardware-related Hand Solo nodes | EQUIVALENT | The hardware `omron_handsolo` service was not started at all; only the virtual simulation/workspace services were launched. |
| 3. Docker Compose up | DONE | Official virtual warehouse started successfully. |
| 4. Create `hand_solo_virtual_nav` and `hs_waypoint_follower` | DONE | Package/node exist and build. |
| 5. Create `rviz`, `config`, `launch` folders | DONE | Present in repository. |
| 6. Place `pa_rviz_mapping.rviz` | DONE | Present in `rviz/`. |
| 7. Place `pa_slam_params.yaml` | DONE | Present in `config/`. |
| 8. Identify SLAM topics and edit config | DONE | Live topics verified; `/virtual_hand_solo/scan` configured. |
| 9. Run `ros2 run rqt_tf_tree rqt_tf_tree` and configure frames | DONE | Exact command run during mapping; GUI capture stored in `docs/evidence/lab05_rqt_tf_tree.png`. |
| 10. Place `mapping_launch.py` | DONE | Present in `launch/`. |
| 11. Add package.xml dependencies | DONE | Required launch, SLAM, RViz, TF and test dependencies included. |
| 12. Update setup.py data files/entry point | DONE | Launch/config/RViz resources install correctly. |
| 13. Build package and source workspace | DONE | Built in official ROS2 Jazzy workspace. |
| 14. `ros2 launch hand_solo_virtual_nav mapping_launch.py` | DONE | SLAM Toolbox and RViz launched successfully. |
| 15. Drive robot, map warehouse, save `pa_warehouse_map_01` | DONE | Robot driven with real `/cmd_vel`; SLAM map saved successfully. |
| 15. Save both map files in GitHub | DONE | `hand_solo_virtual_nav/maps/pa_warehouse_map_01.pgm` and `.yaml` are both on main. |

## Final evidence location

- `docs/evidence/` - exact Lab 04 multi-node and Lab 05 rqt GUI evidence
- `hand_solo_virtual_nav/maps/` - generated `.pgm` and `.yaml` map files
- `docs/RUNTIME_EVIDENCE.md` - runtime evidence summary
- GitHub Actions exact verification run: https://github.com/lephuc2730/IRS_2026_GROUP5/actions/runs/37431121395
