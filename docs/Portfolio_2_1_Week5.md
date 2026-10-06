# Portfolio 2.1: Pine-Apple ROS2 Communication Hub

## Section 1: Design

### ROS2 Topic Exploration

The captured Week 5 topic-list evidence shows **75 active ROS2 topics** in the Pine-Apple warehouse simulation. The topic names suggest their purpose. Topics containing `cmd_vel` are related to robot velocity commands, `odom` is related to robot odometry, `scan` is laser sensor data, and `tf` / `tf_static` provide coordinate transformations.

Sensor-related examples are `/virtual_hand_solo/scan`, `/virtual_hand_solo/odom`, `/odom`, and `/joint_states`. Command-related examples are `/cmd_vel`, `/amr/cmd_vel`, `/cmd_vel_nav`, and `/cmd_vel_teleop`. Status-related examples include `/diagnostics`, `/hmi/unified_status`, and `/status_updates`.

From the supplied topic-list screenshot, `/hmi/unified_status` is the strongest PLC/HMI status candidate by name. However, the lab requires the correct topic to be confirmed by echoing a JSON payload containing `stamp`, `box`, and `counts`. The included `plc_topic_probe` node checks likely String topics for that structure.

### Package Structure Analysis

The `ament_python` package contains `package.xml`, `setup.py`, `setup.cfg`, `LICENSE`, a resource marker, a test folder and the Python module folder. `package.xml` describes the ROS2 package, including dependencies. `setup.py` installs the Python code and registers console-script entry points so commands such as `ros2 run pa_warehouse_status pineapple_gossip_bot` can find the node.

### Publisher-subscriber architecture

```text
PLC / HMI JSON
     |
     v
PLC status topic
     |
     v
plc_hmi_listener

pineapple_gossip_bot
     |
     v
/status_updates
     |
     v
Robot HMI
```

## Section 2: Execution

Complete code is stored in:

- `pa_warehouse_status/pa_warehouse_status/pineapple_gossip_bot.py`
- `pa_warehouse_status/pa_warehouse_status/plc_hmi_listener.py`
- `pa_warehouse_status/pa_warehouse_status/plc_topic_probe.py`

The publisher sends status messages to `status_updates` every two seconds. The listener parses the JSON fields required by the lab: timestamp, box weight, location, and big/medium/small/total counts.

The required Robot HMI screenshot must come from the running course simulation and is therefore not fabricated here.

## Section 3: Reflections

### Colcon workspace

A colcon workspace is a folder structure used to organise, build and install ROS2 packages. Source packages sit inside the `src` folder. `colcon build` creates `build`, `install`, and `log` folders. After building, `source install/local_setup.bash` updates the environment so ROS2 can discover the package and its executables.

### Nodes

A ROS2 node is an individual program that performs a focused task. In Week 5, `pineapple_gossip_bot` publishes HMI status messages while `plc_hmi_listener` receives and parses PLC data. Separating these tasks makes the system easier to test, understand and replace.

### Topics

A ROS2 topic is a named channel for continuous asynchronous communication. Publishers send messages and subscribers receive them without needing to know each other directly. Examples in this project include `/status_updates`, `/cmd_vel`, and `/virtual_hand_solo/scan`.

### Messages

A ROS2 message defines the data structure sent through a topic. The Week 5 status communication uses `std_msgs/msg/String`. The PLC listener expects JSON text inside the String `data` field and then parses it into Python objects.

### Services

A ROS2 service provides request-response communication. It is suitable for short operations where one node sends a request and receives one result, rather than receiving a continuous stream.

### Actions

A ROS2 action is used for longer-running goals that can provide feedback and can be cancelled. Navigation to a waypoint is a common example because the robot can report progress before returning a final result.
