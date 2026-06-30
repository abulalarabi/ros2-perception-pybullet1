#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
)

from robot_interfaces.msg import ControlMode
from robot_interfaces.srv import SetControlMode


class ModeManager(Node):

    def __init__(self):
        super().__init__('mode_manager')

        # Start in manual mode for safety.
        self.current_mode = ControlMode.MANUAL

        # Keep the latest mode available for nodes that start later.
        mode_qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        self.mode_publisher = self.create_publisher(
            ControlMode,
            '/control_mode',
            mode_qos,
        )

        self.mode_service = self.create_service(
            SetControlMode,
            '/set_control_mode',
            self.set_mode_callback,
        )

        self.publish_current_mode()

        self.get_logger().info(
            f'Mode manager started in '
            f'{self.mode_to_string(self.current_mode)} mode.'
        )

    def set_mode_callback(self, request, response):
        requested_mode = request.mode

        valid_modes = [
            ControlMode.MANUAL,
            ControlMode.AUTONOMOUS,
            ControlMode.PAUSED,
            ControlMode.EMERGENCY_STOP,
        ]

        if requested_mode not in valid_modes:
            response.success = False
            response.message = (
                f'Invalid control mode: {requested_mode}'
            )

            self.get_logger().warning(response.message)
            return response

        previous_mode = self.current_mode
        self.current_mode = requested_mode

        self.publish_current_mode()

        response.success = True
        response.message = (
            f'Control mode changed from '
            f'{self.mode_to_string(previous_mode)} to '
            f'{self.mode_to_string(self.current_mode)}.'
        )

        self.get_logger().info(response.message)

        return response

    def publish_current_mode(self):
        message = ControlMode()
        message.mode = self.current_mode

        self.mode_publisher.publish(message)

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

    node = ModeManager()

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