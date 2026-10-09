#!/usr/bin/env python3
import math
import time

import rclpy
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose


# --- Helper function to build a PoseStamped ---
def make_pose(x: float, y: float, yaw: float) -> PoseStamped:
    """
    Create a PoseStamped (position + orientation) in the 'map' frame.
    - x, y are coordinates in meters
    - yaw is robot orientation (heading) in radians
    """
    ps = PoseStamped()
    ps.header.frame_id = 'map'  # always use 'map' for navigation goals
    ps.pose.position.x = x
    ps.pose.position.y = y

    # Convert yaw (in radians) into quaternion (needed by ROS2)
    half = yaw * 0.5
    ps.pose.orientation.z = math.sin(half)
    ps.pose.orientation.w = math.cos(half)
    return ps


def main():
    # 1. Initialise ROS2 and create a node
    rclpy.init()
    node = rclpy.create_node('hs_waypoint_follower_nav2pose')

    # 2. Create an ActionClient for the NavigateToPose action
    client = ActionClient(node, NavigateToPose, 'navigate_to_pose')

    # --- Function to send a goal and wait for result ---
    def send_and_wait(pose: PoseStamped) -> bool:
        node.get_logger().info('Waiting for Nav2 action server...')
        client.wait_for_server()

        # Update timestamp (required in headers)
        pose.header.stamp = node.get_clock().now().to_msg()

        # Wrap pose in a NavigateToPose goal message
        goal = NavigateToPose.Goal()
        goal.pose = pose

        # Simple feedback callback: prints distance left to target
        def feedback_cb(fb):
            try:
                dist = fb.feedback.distance_remaining
                node.get_logger().info(f'Distance remaining: {dist:.2f} m')
            except Exception:
                pass  # ignore if feedback doesn't have distance

        # Send the goal
        send_future = client.send_goal_async(goal, feedback_callback=feedback_cb)
        rclpy.spin_until_future_complete(node, send_future)
        handle = send_future.result()

        if not handle or not handle.accepted:
            node.get_logger().error('Goal was rejected!')
            return False

        # Wait until navigation is finished
        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(node, result_future)
        result = result_future.result()

        if result is None:
            node.get_logger().error('No result returned.')
            return False

        # A finished goal is not always a successful one - check the status
        if result.status != GoalStatus.STATUS_SUCCEEDED:
            node.get_logger().error(f'Goal failed (status {result.status}, '
                                    f'error code {result.result.error_code})')
            return False

        node.get_logger().info('Goal reached successfully!')
        return True

    # --- Hard-coded waypoints for this lab. Edit this section in the code and make it your own ---

    # --- Group 5 patrol route for Lab 06 ---
    # Coordinates are in the Week 6 map frame. These points were selected
    # from the mapped free-space region and can be adjusted from RViz using
    # the Publish Point tool if the warehouse map is regenerated.
    waypoints = [
        ('Waypoint 1', make_pose(0.10, -0.50, 0.0)),
        ('Waypoint 2', make_pose(0.75, 0.00, math.pi / 2.0)),
        ('Waypoint 3', make_pose(0.00, 0.60, math.pi)),
        ('Home',       make_pose(0.15, -0.15, -math.pi / 2.0)),
    ]
    wait_seconds = 3.0

    # Visit each waypoint in sequence and pause between goals.
    for index, (name, pose) in enumerate(waypoints, start=1):
        node.get_logger().info(
            f'Sending {name} ({index}/{len(waypoints)}): '
            f'x={pose.pose.position.x:.2f}, y={pose.pose.position.y:.2f}'
        )

        if not send_and_wait(pose):
            node.get_logger().error(
                f'{name} failed. Stopping the patrol mission.'
            )
            break

        if index < len(waypoints):
            node.get_logger().info(
                f'Waiting {wait_seconds:.0f} seconds before the next waypoint...'
            )
            time.sleep(wait_seconds)


    # --- Your custom code ends here ---

    # 6. Shutdown node and ROS2
    node.get_logger().info('Navigation sequence complete. Shutting down.')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()