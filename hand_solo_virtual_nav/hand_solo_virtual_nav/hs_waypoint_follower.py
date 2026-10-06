#!/usr/bin/env python3

"""Starter node created for the Week 6 hand_solo_virtual_nav package."""

import rclpy
from rclpy.node import Node


class HsWaypointFollower(Node):
    """Starter waypoint-follower node for later navigation activities."""

    def __init__(self):
        super().__init__('hs_waypoint_follower')
        self.get_logger().info(
            'Hand Solo waypoint follower package is ready for mapping/navigation.'
        )


def main(args=None):
    rclpy.init(args=args)
    node = HsWaypointFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
