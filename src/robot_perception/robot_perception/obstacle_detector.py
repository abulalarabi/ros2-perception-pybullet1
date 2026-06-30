#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from robot_interfaces.msg import ObstacleInfo


class ObstacleDetector(Node):

    def __init__(self):
        super().__init__('obstacle_detector')

        self.robot_pose = None
        self.obstacle_pose = None

        self.robot_pose_subscription = self.create_subscription(
            PoseStamped,
            '/robot/pose',
            self.robot_pose_callback,
            10,
        )

        self.obstacle_pose_subscription = self.create_subscription(
            PoseStamped,
            '/simulation/obstacle_pose',
            self.obstacle_pose_callback,
            10,
        )

        self.obstacle_publisher = self.create_publisher(
            ObstacleInfo,
            '/perception/obstacle',
            10,
        )

        self.detection_timer = self.create_timer(
            0.1,
            self.publish_obstacle_detection,
        )

        self.get_logger().info(
            'Obstacle detector node started.'
        )

    def robot_pose_callback(self, message):
        self.robot_pose = message

    def obstacle_pose_callback(self, message):
        self.obstacle_pose = message

    def publish_obstacle_detection(self):
        if self.robot_pose is None or self.obstacle_pose is None:
            return

        robot_x = self.robot_pose.pose.position.x
        robot_y = self.robot_pose.pose.position.y

        obstacle_x = self.obstacle_pose.pose.position.x
        obstacle_y = self.obstacle_pose.pose.position.y

        # Displacement expressed in the world frame.
        dx = obstacle_x - robot_x
        dy = obstacle_y - robot_y

        orientation = self.robot_pose.pose.orientation

        # Convert the robot quaternion into yaw.
        siny_cosp = 2.0 * (
            orientation.w * orientation.z
            + orientation.x * orientation.y
        )

        cosy_cosp = 1.0 - 2.0 * (
            orientation.y * orientation.y
            + orientation.z * orientation.z
        )

        robot_yaw = math.atan2(
            siny_cosp,
            cosy_cosp,
        )

        # Transform the world-frame displacement into the robot frame.
        relative_x = (
            math.cos(robot_yaw) * dx
            + math.sin(robot_yaw) * dy
        )

        relative_y = (
            -math.sin(robot_yaw) * dx
            + math.cos(robot_yaw) * dy
        )

        distance = math.sqrt(
            relative_x ** 2
            + relative_y ** 2
        )

        bearing = math.atan2(
            relative_y,
            relative_x,
        )

        field_of_view = math.radians(120.0)
        maximum_detection_distance = 2.5

        detected = (
            relative_x > 0.0
            and abs(bearing) <= field_of_view / 2.0
            and distance <= maximum_detection_distance
        )

        message = ObstacleInfo()

        message.detected = detected
        message.distance = distance
        message.bearing = bearing
        message.relative_x = relative_x
        message.relative_y = relative_y

        self.obstacle_publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)

    node = ObstacleDetector()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()