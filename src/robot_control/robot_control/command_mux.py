#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from robot_interfaces.msg import ControlMode


class CommandMux(Node):

    def __init__(self):
        super().__init__('command_mux')

        self.current_mode = ControlMode.MANUAL

        self.latest_manual_command = Twist()
        self.latest_autonomous_command = Twist()

        self.manual_subscription = self.create_subscription(
            Twist,
            '/cmd_vel/manual',
            self.manual_command_callback,
            10,
        )

        self.autonomous_subscription = self.create_subscription(
            Twist,
            '/cmd_vel/autonomous',
            self.autonomous_command_callback,
            10,
        )

        self.mode_subscription = self.create_subscription(
            ControlMode,
            '/control_mode',
            self.mode_callback,
            10,
        )

        self.output_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10,
        )

        self.publish_timer = self.create_timer(
            0.05,
            self.publish_selected_command,
        )

        self.get_logger().info(
            'Command mux started in MANUAL mode.'
        )

    def manual_command_callback(self, message):
        self.latest_manual_command = message

    def autonomous_command_callback(self, message):
        self.latest_autonomous_command = message

    def mode_callback(self, message):
        self.current_mode = message.mode

        self.get_logger().info(
            f'Control mode changed to {self.mode_to_string(message.mode)}.'
        )

    def publish_selected_command(self):
        command = Twist()

        if self.current_mode == ControlMode.MANUAL:
            command = self.latest_manual_command

        elif self.current_mode == ControlMode.AUTONOMOUS:
            command = self.latest_autonomous_command

        elif self.current_mode == ControlMode.PAUSED:
            command = Twist()

        elif self.current_mode == ControlMode.EMERGENCY_STOP:
            command = Twist()

        else:
            command = Twist()

        self.output_publisher.publish(command)

    def mode_to_string(self, mode):
        mode_names = {
            ControlMode.MANUAL: 'MANUAL',
            ControlMode.AUTONOMOUS: 'AUTONOMOUS',
            ControlMode.PAUSED: 'PAUSED',
            ControlMode.EMERGENCY_STOP: 'EMERGENCY_STOP',
        }

        return mode_names.get(mode, 'UNKNOWN')


def main(args=None):
    rclpy.init(args=args)

    node = CommandMux()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()