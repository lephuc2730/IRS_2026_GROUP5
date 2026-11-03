#!/usr/bin/env python3

"""Pine-Apple Grand Challenge state machine.

Coordinates PLC box events, MoveIt arm motion and Nav2 navigation for
continuous Large/Medium/Small warehouse operation.
"""

import json
import math
import re
from collections import deque
from typing import Callable, Deque, Dict, List, Optional

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MotionPlanRequest
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger


class WarehouseMissionController(Node):
    """Grand Challenge controller for continuous autonomous box handling."""

    JOINT_NAMES: List[str] = [
        'joint_1', 'joint_2', 'joint_3',
        'joint_4', 'joint_5', 'joint_6',
    ]
    PLANNING_GROUP = 'tmr_arm'

    # Positions already demonstrated by Group 5 in hs_pick_place.py.
    SAFE_ARM = [0.0, 0.0, 1.57, 0.0, 1.57, 0.0]
    PICK_APPROACH = [0.785, -0.5, 1.2, 0.0, 1.0, 0.0]
    PICK_GRASP = [0.785, -0.8, 1.4, 0.0, 0.8, 0.0]
    PICK_RETRACT = [0.785, -0.3, 1.2, 0.0, 1.0, 0.0]
    PLACE_APPROACH = [-0.785, -0.5, 1.2, 0.0, 1.0, 0.0]

    VALID_CATEGORIES = ('large', 'medium', 'small')

    def __init__(self):
        super().__init__('warehouse_mission_controller')

        self.declare_parameter('plc_topic', '/hmi/unified_status')
        self.declare_parameter('plc_auto_trigger', True)
        self.declare_parameter('require_initialpose', True)
        self.declare_parameter('weight_trigger_without_location', True)
        self.declare_parameter(
            'ready_locations',
            ['ready', 'pickup', 'pick', 'conveyor', 'sorted', 'stop'],
        )
        self.declare_parameter('manual_category', 'large')

        # Pickup/home pose. The robot returns here after every completed box.
        self.declare_parameter('pickup_x', 0.15)
        self.declare_parameter('pickup_y', -0.15)
        self.declare_parameter('pickup_yaw', -math.pi / 2.0)

        # Category-specific shelf poses. The exact judged shelf goals must be
        # confirmed in the live warehouse map before the assessed run.
        self.declare_parameter('large_shelf_x', 0.10)
        self.declare_parameter('large_shelf_y', -0.50)
        self.declare_parameter('large_shelf_yaw', 0.0)
        self.declare_parameter('medium_shelf_x', 0.75)
        self.declare_parameter('medium_shelf_y', 0.00)
        self.declare_parameter('medium_shelf_yaw', math.pi / 2.0)
        self.declare_parameter('small_shelf_x', 0.00)
        self.declare_parameter('small_shelf_y', 0.60)
        self.declare_parameter('small_shelf_yaw', math.pi)

        plc_topic = str(self.get_parameter('plc_topic').value)

        self.move_client = ActionClient(self, MoveGroup, '/move_action')
        self.nav_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

        self.status_pub = self.create_publisher(
            String, '/warehouse/mission_status', 10
        )
        self.gripper_pub = self.create_publisher(
            String, '/warehouse/gripper_command', 10
        )

        self.create_subscription(
            String, plc_topic, self._plc_callback, 10
        )
        self.create_subscription(
            PoseWithCovarianceStamped,
            '/initialpose',
            self._initialpose_callback,
            10,
        )
        self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self._amcl_callback,
            10,
        )

        self.create_service(
            Trigger, '/warehouse/start_cycle', self._manual_start
        )
        self.create_service(
            Trigger, '/warehouse/start_large', self._manual_large
        )
        self.create_service(
            Trigger, '/warehouse/start_medium', self._manual_medium
        )
        self.create_service(
            Trigger, '/warehouse/start_small', self._manual_small
        )
        self.create_service(
            Trigger, '/warehouse/retry_current', self._retry_current
        )
        self.create_service(
            Trigger, '/warehouse/reset_queue', self._reset_queue
        )

        self.pending: Deque[str] = deque()
        self.current_category: Optional[str] = None
        self.failed_category: Optional[str] = None
        self.busy = False
        self.initial_pose_received = False
        self.localized = False
        self.last_counts: Optional[Dict[str, int]] = None
        self.last_weight_signature = None
        self.completed_cycles = 0
        self._timers = []

        if self.get_parameter('require_initialpose').value:
            self._publish_status('WAITING_FOR_JUDGE_INITIAL_POSE')
        else:
            self._publish_status('WAITING_FOR_LOCALIZATION')

        self.get_logger().info(
            'Grand Challenge controller ready. Start controller first, then '
            'set the judge-specified 2D Pose Estimate in RViz.'
        )

    def _publish_status(self, state: str, detail: str = ''):
        payload = {
            'state': state,
            'box': self.current_category,
            'queue': list(self.pending),
            'completed': self.completed_cycles,
        }
        if detail:
            payload['detail'] = detail
        msg = String()
        msg.data = json.dumps(payload)
        self.status_pub.publish(msg)
        self.get_logger().info(
            f'MISSION STATE: {state}'
            + (f' | {detail}' if detail else '')
        )

    def _enqueue_category(self, category: str, source: str):
        category = category.strip().lower()
        if category not in self.VALID_CATEGORIES:
            self.get_logger().warning(
                f'Ignoring unknown box category: {category}'
            )
            return

        self.pending.append(category)
        self.get_logger().info(
            f'Queued {category.upper()} box from {source}. '
            f'Queue={list(self.pending)}'
        )
        if self.busy:
            self._publish_status(
                'BOX_QUEUED_WHILE_BUSY',
                f'{category} from {source}',
            )
        self._maybe_start_next()

    # Judge-selected arbitrary start / AMCL localization.
    def _initialpose_callback(self, _msg: PoseWithCovarianceStamped):
        self.initial_pose_received = True
        self.localized = False
        self._publish_status(
            'LOCALIZING',
            'Judge/start pose received from RViz /initialpose',
        )

    def _amcl_callback(self, _msg: PoseWithCovarianceStamped):
        if (
            self.get_parameter('require_initialpose').value
            and not self.initial_pose_received
        ):
            return

        first_localization = not self.localized
        self.localized = True
        if first_localization:
            self._publish_status('LOCALIZED')
            self._maybe_start_next()

    # Manual fallback / test services.
    def _manual_start(self, _request, response):
        category = str(self.get_parameter('manual_category').value).lower()
        if category not in self.VALID_CATEGORIES:
            response.success = False
            response.message = (
                'manual_category must be large, medium or small.'
            )
            return response

        self._enqueue_category(category, 'manual /warehouse/start_cycle')
        response.success = True
        response.message = f'{category} cycle queued.'
        return response

    def _manual_large(self, _request, response):
        return self._manual_category('large', response)

    def _manual_medium(self, _request, response):
        return self._manual_category('medium', response)

    def _manual_small(self, _request, response):
        return self._manual_category('small', response)

    def _manual_category(self, category, response):
        self._enqueue_category(category, f'manual {category} service')
        response.success = True
        response.message = f'{category} cycle queued.'
        return response

    def _retry_current(self, _request, response):
        if self.busy:
            response.success = False
            response.message = 'Mission is still running.'
            return response
        if self.failed_category is None:
            response.success = False
            response.message = 'No failed box is waiting for retry.'
            return response

        category = self.failed_category
        self.failed_category = None
        self.pending.appendleft(category)
        response.success = True
        response.message = f'Retrying {category} box.'
        self._maybe_start_next()
        return response

    def _reset_queue(self, _request, response):
        if self.busy:
            response.success = False
            response.message = 'Cannot clear queue while mission is running.'
            return response

        self.pending.clear()
        self.failed_category = None
        self.current_category = None
        response.success = True
        response.message = 'Queue cleared.'
        self._publish_status('READY_FOR_BOX')
        return response

    # PLC event detection and Grand Challenge L/M/S classification.
    def _plc_callback(self, msg: String):
        try:
            data = json.loads(msg.data)
        except (json.JSONDecodeError, TypeError) as exc:
            self.get_logger().warning(f'Ignoring malformed PLC JSON: {exc}')
            return

        if not self.get_parameter('plc_auto_trigger').value:
            return

        box = data.get('box') or {}
        counts = data.get('counts') or {}
        detected_from_counts = self._detect_count_increments(counts)

        if detected_from_counts:
            return

        weight = self._parse_weight(box.get('weight_raw'))
        if weight is None:
            return

        location = str(box.get('location', '') or '').strip().lower()
        if not self._location_ready(location):
            return

        category = self._category_from_weight(weight)
        total = self._coerce_int(counts.get('total'))
        signature = (category, round(weight, 3), location, total)
        if signature == self.last_weight_signature:
            return

        self.last_weight_signature = signature
        self._enqueue_category(
            category,
            f'PLC weight={weight:g}, location={location or "n/a"}',
        )

    def _detect_count_increments(self, counts) -> bool:
        current = {
            'large': self._coerce_int(counts.get('big')),
            'medium': self._coerce_int(counts.get('medium')),
            'small': self._coerce_int(counts.get('small')),
        }
        if any(value is None for value in current.values()):
            return False

        if self.last_counts is None:
            self.last_counts = current
            return False

        detected = False
        for category in self.VALID_CATEGORIES:
            delta = current[category] - self.last_counts[category]
            if delta > 0:
                for _ in range(min(delta, 10)):
                    self._enqueue_category(
                        category,
                        f'PLC {category} count increment',
                    )
                detected = True

        self.last_counts = current
        return detected

    def _location_ready(self, location: str) -> bool:
        if self.get_parameter('weight_trigger_without_location').value:
            return True
        tokens = [
            str(value).strip().lower()
            for value in self.get_parameter('ready_locations').value
        ]
        return any(token and token in location for token in tokens)

    @staticmethod
    def _parse_weight(value) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        if value is None:
            return None
        match = re.search(r'-?\d+(?:\.\d+)?', str(value))
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    @staticmethod
    def _coerce_int(value) -> Optional[int]:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if value is None:
            return None
        match = re.search(r'-?\d+', str(value))
        if not match:
            return None
        try:
            return int(match.group(0))
        except ValueError:
            return None

    @staticmethod
    def _category_from_weight(weight: float) -> str:
        # Rubric: Large >10 kg, Medium 5-10 kg, Small <5 kg.
        if weight > 10.0:
            return 'large'
        if weight >= 5.0:
            return 'medium'
        return 'small'

    # Grand Challenge state machine.
    def _maybe_start_next(self):
        if self.busy:
            return

        if (
            self.get_parameter('require_initialpose').value
            and not self.initial_pose_received
        ):
            self._publish_status('WAITING_FOR_JUDGE_INITIAL_POSE')
            return

        if not self.localized:
            self._publish_status('WAITING_FOR_LOCALIZATION')
            return

        if not self.pending:
            self._publish_status('READY_FOR_BOX')
            return

        self.current_category = self.pending.popleft()
        self.failed_category = None
        self.busy = True

        self._publish_status(
            'SAFE_ARM_BEFORE_PICKUP',
            f'Preparing {self.current_category} box cycle',
        )
        self._run_arm_sequence(
            [self.SAFE_ARM],
            0,
            lambda: self._navigate(
                'PICKUP',
                self._pickup_pose(),
                self._after_arrive_pickup,
            ),
        )

    def _after_arrive_pickup(self):
        self._publish_status(
            f'PICKING_{self.current_category.upper()}'
        )
        self._run_arm_sequence(
            [self.PICK_APPROACH, self.PICK_GRASP],
            0,
            self._after_grasp_position,
        )

    def _after_grasp_position(self):
        self._gripper_hook('CLOSE')
        self._schedule(
            0.5,
            lambda: self._run_arm_sequence(
                [self.PICK_RETRACT, self.SAFE_ARM],
                0,
                self._after_safe_retract,
            ),
        )

    def _after_safe_retract(self):
        category = self.current_category
        if category is None:
            self._fail('No active box category after pick')
            return

        self._publish_status(
            'ARM_RETRACTED_SAFE',
            f'{category} box ready for base navigation',
        )
        self._navigate(
            f'{category.upper()}_SHELF',
            self._shelf_pose(category),
            self._after_arrive_shelf,
        )

    def _after_arrive_shelf(self):
        self._publish_status(
            f'PLACING_{self.current_category.upper()}'
        )
        self._run_arm_sequence(
            [self.PLACE_APPROACH],
            0,
            self._release_box,
        )

    def _release_box(self):
        category = self.current_category or 'unknown'
        self._gripper_hook('OPEN')
        self._publish_status(
            'BOX_RELEASED_ON_SHELF',
            f'{category} box released; holding briefly for placement verification',
        )
        self._schedule(
            2.0,
            lambda: self._run_arm_sequence(
                [self.SAFE_ARM],
                0,
                self._after_place_retract,
            ),
        )

    def _after_place_retract(self):
        self._publish_status(
            'ARM_RETRACTED_AFTER_PLACE',
            'Returning to pickup/home for next box',
        )
        self._navigate(
            'PICKUP_RETURN',
            self._pickup_pose(),
            self._complete_cycle,
        )

    def _complete_cycle(self):
        category = self.current_category or 'unknown'
        self.completed_cycles += 1
        self._publish_status(
            'BOX_COMPLETE',
            f'{category} box placed; robot returned to pickup',
        )
        self.current_category = None
        self.busy = False
        self._schedule(0.5, self._maybe_start_next)

    def _fail(self, reason: str):
        failed = self.current_category
        self.get_logger().error(reason)
        self.busy = False
        self.failed_category = failed
        self.current_category = None
        self._publish_status(
            'FAILED',
            f'{reason}; failed_box={failed}; use /warehouse/retry_current',
        )

    def _gripper_hook(self, command: str):
        """Publish a hook for the simulator/hardware gripper adapter.

        Captured Group 5 runtime evidence contains MoveIt and Nav2 actions but
        no gripper action server. This explicit hook can be bridged to the
        simulator's actual grasp interface after it is identified at runtime.
        """
        msg = String()
        msg.data = command
        self.gripper_pub.publish(msg)
        self.get_logger().info(f'GRIPPER HOOK: {command}')

    # MoveIt helpers.
    def _run_arm_sequence(
        self,
        sequence: List[List[float]],
        index: int,
        on_complete: Callable[[], None],
    ):
        if index >= len(sequence):
            on_complete()
            return

        if not self.move_client.wait_for_server(timeout_sec=2.0):
            self._fail('MoveIt /move_action server unavailable')
            return

        goal = self._move_goal(sequence[index])
        self.get_logger().info(
            f'Arm waypoint {index + 1}/{len(sequence)}'
        )
        send_future = self.move_client.send_goal_async(goal)
        send_future.add_done_callback(
            lambda future: self._arm_goal_response(
                future, sequence, index, on_complete
            )
        )

    def _arm_goal_response(
        self, future, sequence, index, on_complete
    ):
        handle = future.result()
        if handle is None or not handle.accepted:
            self._fail(f'Arm waypoint {index + 1} rejected')
            return

        result_future = handle.get_result_async()
        result_future.add_done_callback(
            lambda future: self._arm_result(
                future, sequence, index, on_complete
            )
        )

    def _arm_result(self, future, sequence, index, on_complete):
        result = future.result()
        if result is None or result.status != GoalStatus.STATUS_SUCCEEDED:
            status = None if result is None else result.status
            moveit_error = None
            if result is not None:
                try:
                    moveit_error = result.result.error_code.val
                except Exception:
                    pass
            self._fail(
                f'Arm waypoint {index + 1} failed '
                f'(status={status}, moveit_error={moveit_error})'
            )
            return

        self._schedule(
            0.35,
            lambda: self._run_arm_sequence(
                sequence, index + 1, on_complete
            ),
        )

    def _move_goal(self, joints: List[float]) -> MoveGroup.Goal:
        goal = MoveGroup.Goal()
        request = MotionPlanRequest()
        request.group_name = self.PLANNING_GROUP
        request.num_planning_attempts = 10
        request.allowed_planning_time = 5.0
        request.max_velocity_scaling_factor = 0.45
        request.max_acceleration_scaling_factor = 0.40

        constraints = Constraints()
        for name, value in zip(self.JOINT_NAMES, joints):
            constraint = JointConstraint()
            constraint.joint_name = name
            constraint.position = value
            constraint.tolerance_above = 0.01
            constraint.tolerance_below = 0.01
            constraint.weight = 1.0
            constraints.joint_constraints.append(constraint)

        request.goal_constraints.append(constraints)
        goal.request = request
        goal.planning_options.plan_only = False
        return goal

    # Nav2 helpers.
    def _navigate(
        self,
        label: str,
        pose: PoseStamped,
        on_complete: Callable[[], None],
    ):
        if not self.nav_client.wait_for_server(timeout_sec=2.0):
            self._fail('Nav2 /navigate_to_pose server unavailable')
            return

        self._publish_status(f'NAVIGATING_{label}')
        pose.header.stamp = self.get_clock().now().to_msg()

        goal = NavigateToPose.Goal()
        goal.pose = pose

        self.get_logger().info(
            f'Nav2 goal {label}: '
            f'x={pose.pose.position.x:.2f}, '
            f'y={pose.pose.position.y:.2f}'
        )

        send_future = self.nav_client.send_goal_async(
            goal,
            feedback_callback=lambda feedback: self._nav_feedback(
                label, feedback
            ),
        )
        send_future.add_done_callback(
            lambda future: self._nav_goal_response(
                future, label, on_complete
            )
        )

    def _nav_feedback(self, label, feedback):
        try:
            distance = feedback.feedback.distance_remaining
            self.get_logger().debug(
                f'{label}: {distance:.2f} m remaining'
            )
        except Exception:
            pass

    def _nav_goal_response(self, future, label, on_complete):
        handle = future.result()
        if handle is None or not handle.accepted:
            self._fail(f'Nav2 {label} goal rejected')
            return

        result_future = handle.get_result_async()
        result_future.add_done_callback(
            lambda future: self._nav_result(
                future, label, on_complete
            )
        )

    def _nav_result(self, future, label, on_complete):
        result = future.result()
        if result is None or result.status != GoalStatus.STATUS_SUCCEEDED:
            status = None if result is None else result.status
            self._fail(f'Nav2 {label} failed (status={status})')
            return

        self.get_logger().info(f'Nav2 {label} reached successfully')
        self._schedule(0.35, on_complete)

    def _pickup_pose(self) -> PoseStamped:
        return self._make_pose(
            float(self.get_parameter('pickup_x').value),
            float(self.get_parameter('pickup_y').value),
            float(self.get_parameter('pickup_yaw').value),
        )

    def _shelf_pose(self, category: str) -> PoseStamped:
        prefix = f'{category}_shelf'
        return self._make_pose(
            float(self.get_parameter(f'{prefix}_x').value),
            float(self.get_parameter(f'{prefix}_y').value),
            float(self.get_parameter(f'{prefix}_yaw').value),
        )

    @staticmethod
    def _make_pose(x: float, y: float, yaw: float) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.pose.position.x = x
        pose.pose.position.y = y
        half = yaw * 0.5
        pose.pose.orientation.z = math.sin(half)
        pose.pose.orientation.w = math.cos(half)
        return pose

    def _schedule(self, delay: float, callback: Callable[[], None]):
        """Run a one-shot callback without blocking ROS subscriptions/actions."""
        timer = None

        def wrapped():
            timer.cancel()
            try:
                self._timers.remove(timer)
            except ValueError:
                pass
            callback()

        timer = self.create_timer(delay, wrapped)
        self._timers.append(timer)


def main(args=None):
    rclpy.init(args=args)
    node = WarehouseMissionController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Interrupted by user.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
