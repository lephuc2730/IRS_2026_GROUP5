# IRS_2026_GROUP5 - Pine-Apple Grand Challenge

Group 5 integration project for **12059 Industrial Robots and Systems**.

The Grand Challenge controller connects the semester components into one continuous workflow:

```text
Judge places robot at arbitrary start
        |
        v
RViz 2D Pose Estimate -> AMCL localisation
        |
        v
PLC/HMI deploys + sorts box and updates L/M/S counts
        |
        v
Grand Challenge controller detects Large / Medium / Small
        |
        v
Nav2 -> pickup area
        |
        v
MoveIt -> pick approach / grasp pose
        |
        v
Arm retracts to SAFE travel position
        |
        v
Nav2 -> category-specific shelf
        |       (lidar costmaps handle dynamic obstacles)
        v
MoveIt -> place
        |
        v
Arm retracts -> Nav2 returns to pickup
        |
        v
Next queued box automatically
```

The controller is designed for **continuous Large -> Medium -> Small operation** rather than restarting the system for every box.

## Grand Challenge files

- `pa_warehouse_status/pa_warehouse_status/warehouse_mission_controller.py` - mission state machine.
- `pa_warehouse_status/config/grand_challenge_params.yaml` - pickup and L/M/S shelf goals.
- `pa_warehouse_status/launch/grand_challenge.launch.py` - one-command controller launch.
- `scripts/grand_challenge_preflight.sh` - checks PLC, localisation, lidar, MoveIt and Nav2 interfaces.
- `hand_solo_virtual_nav/config/pa_nav2_params.yaml` - Nav2 config with lidar obstacle layers and arbitrary-start localisation support.

## Tomorrow: build

Use the Grand Challenge branch:

```bash
cd ~/irs_ws/src/IRS_2026_GROUP5
git fetch
git checkout fix/integrated-warehouse-cycle
git pull

cd ~/irs_ws
colcon build --packages-select pa_warehouse_status hand_solo_virtual_nav hand_solo_arm
source install/setup.bash
```

If your workspace is mounted at `/workspace/irs_ws`, use that path instead.

## Start the course system

The current course `omron_handsolo` full-system launch already starts the arm, MoveIt, mobile base and Nav2. If your Docker `compose.yaml` uses that full launch, **do not start a second Nav2 stack from this repository at the same time**.

Once the course simulator and Hand Solo stack are running, check the core interfaces:

```bash
cd ~/irs_ws/src/IRS_2026_GROUP5
bash scripts/grand_challenge_preflight.sh
```

The important interfaces are:

```text
/hmi/unified_status
/amcl_pose
/virtual_hand_solo/scan
/move_action
/navigate_to_pose
```

## Launch the Grand Challenge controller

```bash
source ~/irs_ws/install/setup.bash
ros2 launch pa_warehouse_status grand_challenge.launch.py
```

In another terminal:

```bash
ros2 topic echo /warehouse/mission_status
```

### Arbitrary judge-specified start position

Before the first box cycle, use **2D Pose Estimate** in RViz and click/drag at the robot's actual judge-specified start pose.

The controller intentionally waits for `/initialpose` and an AMCL update before accepting the first queued mission.

## PLC box classification

The controller first looks for PLC count changes:

```text
counts.big     -> Large
counts.medium  -> Medium
counts.small   -> Small
```

It also supports the Grand Challenge weight rules as a fallback:

```text
weight > 10 kg  -> Large
5-10 kg         -> Medium
weight < 5 kg   -> Small
```

PLC automatic triggering is enabled in `grand_challenge_params.yaml`.

## Continuous state machine

Typical states are:

```text
WAITING_FOR_JUDGE_INITIAL_POSE
LOCALIZING
READY_FOR_BOX
SAFE_ARM_BEFORE_PICKUP
NAVIGATING_PICKUP
PICKING_LARGE / PICKING_MEDIUM / PICKING_SMALL
ARM_RETRACTED_SAFE
NAVIGATING_LARGE_SHELF / MEDIUM_SHELF / SMALL_SHELF
PLACING_LARGE / PLACING_MEDIUM / PLACING_SMALL
ARM_RETRACTED_AFTER_PLACE
NAVIGATING_PICKUP_RETURN
BOX_COMPLETE
READY_FOR_BOX
```

If the next PLC box arrives while a mission is running, it is queued and starts automatically after the current box completes.

## Manual fallback for testing

These services let you test the state machine without waiting for the PLC:

```bash
ros2 service call /warehouse/start_large std_srvs/srv/Trigger "{}"
ros2 service call /warehouse/start_medium std_srvs/srv/Trigger "{}"
ros2 service call /warehouse/start_small std_srvs/srv/Trigger "{}"
```

If an action fails:

```bash
ros2 service call /warehouse/retry_current std_srvs/srv/Trigger "{}"
```

## Dynamic obstacle avoidance ("Kevin")

The Nav2 configuration uses the live `/virtual_hand_solo/scan` lidar in both local and global obstacle costmaps. Obstacles are marked and cleared from live scan data while the local planner replans/controls the robot around them.

Do not hard-code a path around Kevin. Let Nav2 react to the live obstacle.

## IMPORTANT: calibrate pickup and shelf poses before assessment

The values currently in `grand_challenge_params.yaml` are **provisional Group 5 waypoint coordinates**. They are not proven to be the final Large, Medium and Small shelf positions in the exact warehouse map used by the judges.

Before the assessed run, use RViz on the actual running map to record:

- pickup/conveyor base pose
- Large shelf base pose
- Medium shelf base pose
- Small shelf base pose

Then update only `grand_challenge_params.yaml`; the state machine code does not need to change.

## IMPORTANT: physical box grasp

The official runtime probe confirms that MoveIt and Nav2 are available, but it exposes **no obvious grip/pick/attach/vacuum action or service**. The previously observed `/virtual_hand_solo/han_shot_first` topic was also confirmed to be a `sensor_msgs/msg/Image` camera topic from `static_image_publisher`, so it must **not** be used as a gripper command.

The controller publishes:

```text
/warehouse/gripper_command = CLOSE
/warehouse/gripper_command = OPEN
```

as explicit integration hooks at the correct points in the state machine, but they are not claimed to actuate a physical/simulated gripper.

This matches the Week 10 course exercise, which controls the programmatic pick/carry/place sequence through MoveIt's `/move_action` and recorded joint positions rather than defining a separate ROS gripper action. For tomorrow's demonstration, verify how the current Pine-Apple simulator represents box attachment during the arm motion before claiming a physical grasp.

## Existing semester packages

### PLC / ROS2 communication

`pa_warehouse_status` also contains:

- `pineapple_gossip_bot`
- `plc_hmi_listener`
- `plc_topic_probe`

The confirmed PLC/HMI status topic is `/hmi/unified_status`.

### Navigation

`hand_solo_virtual_nav` contains mapping, Nav2 configuration, saved Group 5 map files and the earlier waypoint-follower work.

### Manipulation

`hand_solo_arm` contains the Group 5 MoveIt joint-space pick/place sequence used as the basis of the integrated state machine.
