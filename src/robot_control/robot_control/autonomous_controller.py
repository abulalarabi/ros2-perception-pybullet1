#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from robot_interfaces.msg import ObstacleInfo, TargetDetection
from geometry_msgs.msg import Twist

class AutonomousController(Node):

    def __init__(self):
        super().__init__('autonomous_controller')

        self.target_detection = None
        self.obstacle_info = None

        self.target_subscription = self.create_subscription(
            TargetDetection,
            '/perception/target',
            self.target_callback,
            10,
        )

        self.obstacle_subscription = self.create_subscription(
            ObstacleInfo,
            '/perception/obstacle',
            self.obstacle_callback,
            10,
        )

        self.get_logger().info(
            'Autonomous controller node started.'
        )

        self.cmd_vel_publisher = self.create_publisher(
            Twist,
            '/cmd_vel/autonomous',
            10,
        )

        self.control_timer = self.create_timer(
            0.1,
            self.control_loop,
        )

        self.state = 'SEARCH'

        self.stop_distance = 0.6
        self.maximum_linear_speed = 0.5
        self.maximum_angular_speed = 0.8

        self.heading_tolerance = 0.10
        self.obstacle_stop_distance = 0.8

    def target_callback(self, message):
        self.target_detection = message


    def obstacle_callback(self, message):
        self.obstacle_info = message
    
    def control_loop(self):
        command = Twist()

        if self.target_detection is None:
            self.cmd_vel_publisher.publish(command)
            return

        target = self.target_detection
        if (
            self.obstacle_info is not None
            and self.obstacle_info.detected
            and self.obstacle_info.distance <= self.obstacle_stop_distance
        ):
            self.state = 'OBSTACLE_STOP'

            command.linear.x = 0.0
            command.angular.z = 0.0

            self.cmd_vel_publisher.publish(command)
            return

        if not target.detected:
            self.state = 'SEARCH'

        elif target.distance <= self.stop_distance:
            self.state = 'STOP'

        elif abs(target.bearing) > self.heading_tolerance:
            self.state = 'ALIGN'

        else:
            self.state = 'APPROACH'

        if self.state == 'SEARCH':
            command.linear.x = 0.0
            command.angular.z = 0.4

        elif self.state == 'ALIGN':
            command.linear.x = 0.0
            command.angular.z = self.limit_value(
                target.bearing,
                self.maximum_angular_speed,
            )

        elif self.state == 'APPROACH':
            command.linear.x = self.maximum_linear_speed
            command.angular.z = 0.0

        elif self.state == 'STOP':
            command.linear.x = 0.0
            command.angular.z = 0.0

        self.cmd_vel_publisher.publish(command)

    def limit_value(self, value, maximum):
        return max(-maximum, min(value, maximum))


def main(args=None):
    rclpy.init(args=args)

    node = AutonomousController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()