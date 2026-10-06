#!/usr/bin/env python3

"""Publish status strings to the Pine-Apple Robot HMI every two seconds."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class PineappleGossipBot(Node):
    """ROS 2 publisher for the Week 5 status_updates task."""

    def __init__(self):
        super().__init__('pineapple_gossip_bot')
        self.publisher_ = self.create_publisher(String, 'status_updates', 10)
        self.timer = self.create_timer(2.0, self.publish_status)
        self.messages = [
            'Pine-Apple AMR online - warehouse link active.',
            'Hand Solo status: ready for the next warehouse task.',
            'Route check complete - systems nominal.',
            'Group 5 ROS2 communication hub is running.',
        ]
        self.index = 0
        self.get_logger().info('Publishing to /status_updates every 2 seconds.')

    def publish_status(self):
        """Publish the next status message."""
        msg = String()
        msg.data = self.messages[self.index]
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: {msg.data}')
        self.index = (self.index + 1) % len(self.messages)


def main(args=None):
    rclpy.init(args=args)
    node = PineappleGossipBot()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
