#!/usr/bin/env python3

import sys
import termios
import tty

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


class KeyboardTeleop(Node):

    def __init__(self):
        super().__init__('keyboard_teleop')

        self.publisher = self.create_publisher(
            Twist,
            '/cmd_vel/manual',
            10,
        )

        self.linear_speed = 0.4
        self.angular_speed = 0.8

        self.get_logger().info(
            '\nKeyboard teleop started.\n'
            'w: forward\n'
            's: backward\n'
            'a: turn left\n'
            'd: turn right\n'
            'space: stop\n'
            'q: quit\n'
        )

    def get_key(self):
        settings = termios.tcgetattr(sys.stdin)

        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(
                sys.stdin,
                termios.TCSADRAIN,
                settings,
            )

        return key

    def create_command(self, key):
        command = Twist()

        if key == 'w':
            command.linear.x = self.linear_speed

        elif key == 's':
            command.linear.x = -self.linear_speed

        elif key == 'a':
            command.angular.z = self.angular_speed

        elif key == 'd':
            command.angular.z = -self.angular_speed

        elif key == ' ':
            command.linear.x = 0.0
            command.angular.z = 0.0

        return command

    def stop_robot(self):
        command = Twist()
        self.publisher.publish(command)

    def run(self):
        try:
            while rclpy.ok():
                key = self.get_key()

                if key == 'q':
                    self.stop_robot()
                    break

                command = self.create_command(key)
                self.publisher.publish(command)

        except KeyboardInterrupt:
            self.stop_robot()

        finally:
            self.stop_robot()


def main(args=None):
    rclpy.init(args=args)

    node = KeyboardTeleop()

    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()