import rclpy
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped, Twist
from robot_interfaces.msg import TargetDetection

import math

class TargetDetector(Node):
    def __init__(self):
        super().__init__('target_detector')

        self.robot_pose = None
        self.target_pose = None

        self.robot_pose_subscription = self.create_subscription(
            PoseStamped,
            '/robot/pose',
            self.robot_pose_callback,
            10,
        )

        self.target_pose_subscription = self.create_subscription(
            PoseStamped,
            '/simulation/target_pose',
            self.target_pose_callback,
            10,
        )

        self.detection_publisher = self.create_publisher(
            TargetDetection,
            '/perception/target',
            10,
        )

        self.detection_timer = self.create_timer(
            0.1,
            self.publish_target_detection,
        )

        self.get_logger().info(
            'Target Detector Node Started'
        )
    
    def robot_pose_callback(self, message):
        self.robot_pose = message


    def target_pose_callback(self, message):
        self.target_pose = message
    
    def publish_target_detection(self):
        if self.robot_pose is None or self.target_pose is None:
            return

        robot_x = self.robot_pose.pose.position.x
        robot_y = self.robot_pose.pose.position.y

        target_x = self.target_pose.pose.position.x
        target_y = self.target_pose.pose.position.y

        dx = target_x - robot_x
        dy = target_y - robot_y

        orientation = self.robot_pose.pose.orientation

        siny_cosp = 2.0 * (
            orientation.w * orientation.z
            + orientation.x * orientation.y
        )

        cosy_cosp = 1.0 - 2.0 * (
            orientation.y * orientation.y
            + orientation.z * orientation.z
        )

        robot_yaw = math.atan2(siny_cosp, cosy_cosp)

        relative_x = (
            math.cos(robot_yaw) * dx
            + math.sin(robot_yaw) * dy
        )

        relative_y = (
            -math.sin(robot_yaw) * dx
            + math.cos(robot_yaw) * dy
        )

        distance = math.sqrt(
            relative_x ** 2 + relative_y ** 2
        )

        bearing = math.atan2(
            relative_y,
            relative_x,
        )
        field_of_view = math.radians(90.0)
        maximum_detection_distance = 5.0

        detected = (
            relative_x > 0.0
            and abs(bearing) <= field_of_view / 2.0
            and distance <= maximum_detection_distance
        )

        message = TargetDetection()

        message.detected = detected
        message.relative_x = relative_x
        message.relative_y = relative_y
        message.distance = distance
        message.bearing = bearing
        if detected:
            message.confidence = 1.0
        else:
            message.confidence = 0.0

        self.detection_publisher.publish(message)


def main(args = None):
    rclpy.init(args=args)

    node = TargetDetector()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()