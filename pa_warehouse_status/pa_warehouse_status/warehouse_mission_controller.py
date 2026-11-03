#!/usr/bin/env python3

"""Integrated PLC -> MoveIt -> Nav2 warehouse mission controller."""

import json
import math
from typing import Callable, List

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MotionPlanRequest
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger


class WarehouseMissionController(Node):
    """Coordinate PLC status, arm motion, delivery navigation and return home."""

    JOINT_NAMES: List[str] = [
        'joint_1', 'joint_2', 'joint_3',
        'joint_4', 'joint_5', 'joint_6',
    ]
    PLANNING_GROUP = 'tmr_arm'

    # These are the same arm positions already demonstrated in hs_pick_place.py.
    PICK_SEQUENCE = [
        [0.0, 0.0, 1.57, 0.0, 1.57, 0.0],
        [0.785, -0.5, 1.2, 0.0, 1.0, 0.0],
        [0.785, -0.8, 1.4, 0.0, 0.8, 0.0],
        [0.785, -0.3, 1.2, 0.0, 1.0, 0.0],
    ]

    PLACE_SEQUENCE = [
        [-0.785, -0.5, 1.2, 0.0, 1.0, 0.0],
        [0.0, 0.0, 1.57, 0.0, 1.57, 0.0],
    ]

    def __init__(self):
        super().__init__('warehouse_mission_controller')

        self.declare_parameter('plc_topic', '/hmi/unified_status')
        self.declare_parameter('plc_auto_trigger', False)
        self.declare_parameter(
            'ready_locations',
            ['ready', 'pickup', 'pick', 'conveyor'],
        )

        # Delivery and home poses are parameters so they can be adjusted from RViz
        # without editing this file.
        self.declare_parameter('delivery_x', 0.75)
        self.declare_parameter('delivery_y', 0.00)
        self.declare_parameter('delivery_yaw', math.pi / 2.0)
        self.declare_parameter('home_x', 0.15)
        self.declare_parameter('home_y', -0.15)
        self.declare_parameter('home_yaw', -math.pi / 2.0)

        plc_topic = self.get_parameter('plc_topic').value

        self.move_client = ActionClient(self, MoveGroup, '/move_action')
        self.nav_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')

        self.status_pub = self.create_publisher(
            String,
            '/warehouse/mission_status',
            10,
        )

        self.create_subscription(
            String,
            plc_topic,
            self._plc_callback,
            10,
        )

        self.create_service(
            Trigger,
            '/warehouse/start_cycle',
            self._manual_start,
        )

        self.busy = False
        self.last_trigger_signature = None
        self._timers = []

        self._publish_status('IDLE')
        self.get_logger().info(
            'Warehouse mission controller ready. '
            'Manual demo: ros2 service call /warehouse/start_cycle '
            'std_srvs/srv/Trigger "{}"'
        )

    def _publish_status(self, state: str):
        msg = String()
        msg.data = state
        self.status_pub.publish(msg)
        self.get_logger().info(f'MISSION STATE: {state}')

    def _manual_start(self, request, response):
        del request
        if self.busy:
            response.success = False
            response.message = 'Mission is already running.'
            return response

        response.success = True
        response.message = 'Warehouse cycle started.'
        self._start_cycle('manual service trigger')
        return response

    def _plc_callback(self, msg: String):
        """Optionally start one cycle when the PLC reports a ready box."""
        try:
            data = json.loads(msg.data)
            box = data.get('box', {})
            counts = data.get('counts', {})
            stamp = data.get('stamp', {})

            location = str(box.get('location', '')).strip().lower()
            weight = box.get('weight_raw', 'unknown')
            total = counts.get('total', 'unknown')

            self.get_logger().debug(
                f'PLC: location={location}, weight={weight}, total={total}'
            )

            if not self.get_parameter('plc_auto_trigger').value:
                return

            ready_locations = [
                str(v).strip().lower()
                for v in self.get_parameter('ready_locations').value
            ]
            is_ready = any(token and token in location for token in ready_locations)
            if not is_ready or self.busy:
                return

            signature = (
                stamp.get('sec'),
                stamp.get('nanosec'),
                location,
                total,
            )
            if signature == self.last_trigger_signature:
                return

            self.last_trigger_signature = signature
            self._start_cycle(
                f'PLC ready box: location={location}, weight={weight}, total={total}'
            )

        except (json.JSONDecodeError, TypeError, AttributeError) as exc:
            self.get_logger().warning(f'Ignoring malformed PLC message: {exc}')

    def _start_cycle(self, source: str):
        self.busy = True
        self.get_logger().info(f'Starting warehouse cycle from {source}')
        self._publish_status('PICKING')
        self._run_arm_sequence(
            self.PICK_SEQUENCE,
            0,
            lambda: self._navigate('DROPOFF', self._delivery_pose(), self._after_dropoff),
        )

    def _after_dropoff(self):
        self._publish_status('PLACING')
        self._run_arm_sequence(
            self.PLACE_SEQUENCE,
            0,
            lambda: self._navigate('HOME', self._home_pose(), self._complete_cycle),
        )

    def _complete_cycle(self):
        self._publish_status('COMPLETE')
        self.get_logger().info('Full warehouse cycle complete: pick -> drop-off -> home.')
        self._schedule(1.0, self._set_idle)

    def _set_idle(self):
        self.busy = False
        self._publish_status('IDLE')

    def _fail(self, reason: str):
        self.get_logger().error(reason)
        self._publish_status(f'FAILED: {reason}')
        self.busy = False

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

    def _arm_goal_response(self, future, sequence, index, on_complete):
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
            self._fail(f'Arm waypoint {index + 1} failed (status={status})')
            return

        self._schedule(
            0.5,
            lambda: self._run_arm_sequence(
                sequence, index + 1, on_complete
            ),
        )

    def _navigate(self, label: str, pose: PoseStamped, on_complete: Callable[[], None]):
        if not self.nav_client.wait_for_server(timeout_sec=2.0):
            self._fail('Nav2 /navigate_to_pose server unavailable')
            return

        self._publish_status(f'NAVIGATING_{label}')
        pose.header.stamp = self.get_clock().now().to_msg()

        goal = NavigateToPose.Goal()
        goal.pose = pose

        self.get_logger().info(
            f'Nav2 goal {label}: x={pose.pose.position.x:.2f}, '
            f'y={pose.pose.position.y:.2f}'
        )

        send_future = self.nav_client.send_goal_async(goal)
        send_future.add_done_callback(
            lambda future: self._nav_goal_response(future, label, on_complete)
        )

    def _nav_goal_response(self, future, label, on_complete):
        handle = future.result()
        if handle is None or not handle.accepted:
            self._fail(f'Nav2 {label} goal rejected')
            return

        result_future = handle.get_result_async()
        result_future.add_done_callback(
            lambda future: self._nav_result(future, label, on_complete)
        )

    def _nav_result(self, future, label, on_complete):
        result = future.result()
        if result is None or result.status != GoalStatus.STATUS_SUCCEEDED:
            status = None if result is None else result.status
            self._fail(f'Nav2 {label} failed (status={status})')
            return

        self.get_logger().info(f'Nav2 {label} reached successfully')
        self._schedule(0.5, on_complete)

    def _move_goal(self, joints: List[float]) -> MoveGroup.Goal:
        goal = MoveGroup.Goal()
        request = MotionPlanRequest()
        request.group_name = self.PLANNING_GROUP
        request.num_planning_attempts = 10
        request.allowed_planning_time = 5.0
        request.max_velocity_scaling_factor = 0.5
        request.max_acceleration_scaling_factor = 0.5

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

    def _delivery_pose(self) -> PoseStamped:
        return self._make_pose(
            float(self.get_parameter('delivery_x').value),
            float(self.get_parameter('delivery_y').value),
            float(self.get_parameter('delivery_yaw').value),
        )

    def _home_pose(self) -> PoseStamped:
        return self._make_pose(
            float(self.get_parameter('home_x').value),
            float(self.get_parameter('home_y').value),
            float(self.get_parameter('home_yaw').value),
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
        """Run callback later without blocking ROS subscriptions/actions."""
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
