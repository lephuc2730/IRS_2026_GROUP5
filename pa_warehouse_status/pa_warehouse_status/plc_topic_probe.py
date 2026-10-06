#!/usr/bin/env python3

"""Helper node for identifying the PLC JSON status topic in the live lab."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class PlcTopicProbe(Node):
    """Subscribe to likely String status topics and report matching PLC JSON."""

    KEYWORDS = ('plc', 'status', 'hmi', 'response')

    def __init__(self):
        super().__init__('plc_topic_probe')
        self.subscriptions = []
        self.timer = self.create_timer(2.0, self.discover_topics)
        self.seen = set()
        self.get_logger().info('Looking for candidate PLC status topics...')

    def discover_topics(self):
        for topic_name, topic_types in self.get_topic_names_and_types():
            if topic_name in self.seen:
                continue
            if 'std_msgs/msg/String' not in topic_types:
                continue
            if not any(k in topic_name.lower() for k in self.KEYWORDS):
                continue

            self.seen.add(topic_name)
            sub = self.create_subscription(
                String,
                topic_name,
                lambda msg, topic=topic_name: self.check_message(topic, msg),
                10,
            )
            self.subscriptions.append(sub)
            self.get_logger().info(f'Probing {topic_name}')

    def check_message(self, topic_name, msg):
        try:
            data = json.loads(msg.data)
        except (json.JSONDecodeError, TypeError):
            return

        if all(key in data for key in ('stamp', 'box', 'counts')):
            self.get_logger().info(
                f'PLC JSON topic found: {topic_name} | payload={msg.data}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = PlcTopicProbe()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
