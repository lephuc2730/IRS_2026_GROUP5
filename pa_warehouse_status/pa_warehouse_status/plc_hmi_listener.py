#!/usr/bin/env python3

"""Subscribe to a PLC/HMI JSON status topic and parse the Lab 04 fields."""

import json

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class PlcHmiListener(Node):
    """Parse PLC JSON messages containing stamp, box and counts objects."""

    def __init__(self):
        super().__init__('plc_hmi_listener')

        # Candidate from the captured Week 5 topic list.
        # The live lab still needs ros2 topic echo/probe to prove the exact
        # JSON topic. Override this parameter without editing code if needed.
        self.declare_parameter('plc_topic', '/hmi/unified_status')
        plc_topic = (
            self.get_parameter('plc_topic')
            .get_parameter_value()
            .string_value
        )

        self.subscription = self.create_subscription(
            String,
            plc_topic,
            self.listener_callback,
            10,
        )
        self.get_logger().info(f'Listening for PLC status on {plc_topic}')

    def listener_callback(self, msg):
        """Parse and print the JSON fields specified by the Week 5 lab."""
        try:
            data = json.loads(msg.data)
            stamp = data['stamp']
            box = data['box']
            counts = data['counts']

            print('Received PLC status:')
            print(f"  Time: {stamp['sec']}.{stamp['nanosec']}")
            print(f"  Box weight raw: {box['weight_raw']}")
            print(f"  Location: {box['location']}")
            print(
                '  Counts: '
                f"big={counts['big']}, "
                f"medium={counts['medium']}, "
                f"small={counts['small']}, "
                f"total={counts['total']}"
            )
            print()
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            self.get_logger().error(
                f'Failed to parse PLC JSON: {exc}; raw message={msg.data}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = PlcHmiListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
