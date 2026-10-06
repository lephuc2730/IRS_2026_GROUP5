# Portfolio 2.2: Hand Solo's Mapping Mission

## Section 1: Design

### ROS2 topics needed for SLAM Toolbox

The supplied RViz configuration uses `/virtual_hand_solo/scan` for laser scan data and `/virtual_hand_solo/odom` for odometry display. During mapping, SLAM Toolbox publishes the occupancy grid on `/map` and map updates on `/map_updates`. ROS2 transformations are provided through `/tf` and `/tf_static`.

The SLAM parameter file therefore uses:

```yaml
scan_topic: /virtual_hand_solo/scan
```

### Transformation frames needed for SLAM Toolbox

The live official warehouse runtime confirmed these frames:

- `map`
- `virtual_hand_solo/odom`
- `virtual_hand_solo/base_link`
- `virtual_hand_solo/lidar_link`

The LaserScan message header reported `virtual_hand_solo/lidar_link`. A live TF graph recorded during mapping showed the complete chain:

```text
map
  -> virtual_hand_solo/odom
      -> virtual_hand_solo/base_link
          -> virtual_hand_solo/lidar_link
          -> camera_link
```

The final SLAM configuration therefore uses `map_frame: map`, `odom_frame: virtual_hand_solo/odom`, `base_frame: virtual_hand_solo/base_link`, and `scan_topic: /virtual_hand_solo/scan`.

## Section 2: Execution

The final configuration is stored in:

`hand_solo_virtual_nav/config/pa_slam_params.yaml`

The required live TF tree can be inspected with:

```bash
ros2 run rqt_tf_tree rqt_tf_tree
```

A live TF graph and a real SLAM occupancy map were generated in the official unit simulation using the project package. The map was saved successfully as `pa_warehouse_map_01.pgm` and `pa_warehouse_map_01.yaml`.

## Section 3: Reflections

### What technique does SLAM Toolbox use for mapping?

SLAM Toolbox performs 2D mapping using laser scan matching together with a pose-graph representation. As the robot moves, laser scans are matched to estimate relative motion and useful robot poses become nodes in the graph. Constraints connect the poses, including loop-closure constraints when the robot revisits a previously mapped area. Optimising the pose graph reduces accumulated drift and produces a more consistent occupancy-grid map.

### What is a ROS launch file and why do we use it?

A ROS launch file starts and configures several ROS2 processes as one repeatable system. The provided `mapping_launch.py` finds the package share directory, loads the SLAM YAML and RViz configuration, launches `async_slam_toolbox_node` as a lifecycle node, sends the configure and activate lifecycle transitions, and then starts RViz2. This allows the mapping environment to be started with one command instead of manually opening several terminals.

### Launch command

```bash
cd /workspace/irs_ws
colcon build --packages-select hand_solo_virtual_nav
source install/local_setup.bash
ros2 launch hand_solo_virtual_nav mapping_launch.py
```
