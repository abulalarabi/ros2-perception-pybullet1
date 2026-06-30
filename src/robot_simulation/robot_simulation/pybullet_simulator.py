#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import pybullet as pb
import pybullet_data

from geometry_msgs.msg import Twist, PoseStamped
import math

from robot_interfaces.srv import ResetSimulation

class PyBulletSimulator(Node):

    def __init__(self):
        super().__init__('pybullet_simulator')

        # create scene and add physics engine
        self.physics_client = pb.connect(pb.GUI)
        if self.physics_client < 0:
            raise RuntimeError('Failed to connect to PyBullet.')

        pb.setAdditionalSearchPath(pybullet_data.getDataPath())
        pb.setGravity(0.0,0.0,-9.81)

        # blank plane
        self.plane_id = pb.loadURDF('plane.urdf')

        # robot
        self.robot_start_position = [0.0,0.0,0.25]
        self.robot_start_orientation = pb.getQuaternionFromEuler(
            [0.0, 0.0, 0.0]
        )
        self.robot_id = self.create_robot()

        # target
        self.target_position = [3.0, 1.0, 0.20]
        self.target_id = self.create_target()

        # obstacle
        self.obstacle_position = [1.5, 0.3, 0.30]
        self.obstacle_id = self.create_obstacle()

        # set initial velocities
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

        # subscribe to the velocity commander
        self.cmd_vel_subscription = self.create_subscription(
            Twist,  # type of message
            '/cmd_vel', # topic
            self.cmd_vel_callback, # callback function
            10, # QoS
        )

        # publish the robot pose
        self.pose_publisher = self.create_publisher(
            PoseStamped,
            '/robot/pose',
            10,
        )
        # publish every 0.05s
        self.pose_timer = self.create_timer(
            0.05,
            self.publish_robot_pose,    # callback
        )

        # publish target pose
        self.target_pose_publisher = self.create_publisher(
            PoseStamped,
            '/simulation/target_pose',
            10,
        )
        # publish it 10Hz
        self.target_pose_timer = self.create_timer(
            0.1,
            self.publish_target_pose,
        )

        # finally publish the obstacle pose
        self.obstacle_pose_publisher = self.create_publisher(
            PoseStamped,
            '/simulation/obstacle_pose',
            10,
        )
        # similarly 10Hz
        self.obstacle_pose_timer = self.create_timer(
            0.1,
            self.publish_obstacle_pose,
        )

        # Now the reset service
        self.reset_service = self.create_service(
            ResetSimulation, # service description
            '/reset_simulation',    # topic
            self.reset_simulation_callback, # callback
        )

        # timer
        self.physics_timer = self.create_timer(
            1.0 / 240.0,
            self.step_simulation, # callback
        )
        
        self.get_logger().info(
            'PyBullet Simulator Node Started'
        )
    
    def create_robot(self):
        half_extents = [0.3,0.2,0.2]

        collision_shape = pb.createCollisionShape(
            pb.GEOM_BOX,
            halfExtents = half_extents,
        )

        visual_shape = pb.createVisualShape(
            pb.GEOM_BOX,
            halfExtents = half_extents,
            rgbaColor = [0.2, 0.5, 0.9, 1.0],
        )

        robot_id = pb.createMultiBody(
            baseMass = 2.0,
            baseCollisionShapeIndex = collision_shape,
            baseVisualShapeIndex=visual_shape,
            basePosition=self.robot_start_position,
            baseOrientation=self.robot_start_orientation,
        )
        return robot_id

    def create_target(self):
        half_extents = [0.20, 0.20, 0.20]

        collision_shape = pb.createCollisionShape(
            pb.GEOM_BOX,
            halfExtents=half_extents,
        )

        visual_shape = pb.createVisualShape(
            pb.GEOM_BOX,
            halfExtents=half_extents,
            rgbaColor=[1.0, 0.1, 0.1, 1.0],
        )

        target_id = pb.createMultiBody(
            baseMass=0.0,
            baseCollisionShapeIndex=collision_shape,
            baseVisualShapeIndex=visual_shape,
            basePosition=self.target_position,
        )

        return target_id
        
    def create_obstacle(self):
        half_extents = [0.25, 0.50, 0.30]

        collision_shape = pb.createCollisionShape(
            pb.GEOM_BOX,
            halfExtents=half_extents,
        )

        visual_shape = pb.createVisualShape(
            pb.GEOM_BOX,
            halfExtents=half_extents,
            rgbaColor=[0.4, 0.4, 0.4, 1.0],
        )

        obstacle_id = pb.createMultiBody(
            baseMass=0.0,
            baseCollisionShapeIndex=collision_shape,
            baseVisualShapeIndex=visual_shape,
            basePosition=self.obstacle_position,
        )

        return obstacle_id

    def step_simulation(self):
        position, orientation = pb.getBasePositionAndOrientation(
            self.robot_id
        )

        yaw = pb.getEulerFromQuaternion(orientation)[2]
        world_velocity_x = self.linear_velocity * math.cos(yaw)
        world_velocity_y = self.linear_velocity * math.sin(yaw)

        pb.resetBaseVelocity(
            self.robot_id,
            linearVelocity=[
                world_velocity_x,
                world_velocity_y,
                0.0,
            ],
            angularVelocity=[
                0.0,
                0.0,
                self.angular_velocity,
            ],
        )

        pb.stepSimulation()

    def publish_robot_pose(self):
        position, orientation = pb.getBasePositionAndOrientation(
            self.robot_id
        )

        message = PoseStamped()

        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'world'

        message.pose.position.x = position[0]
        message.pose.position.y = position[1]
        message.pose.position.z = position[2]

        message.pose.orientation.x = orientation[0]
        message.pose.orientation.y = orientation[1]
        message.pose.orientation.z = orientation[2]
        message.pose.orientation.w = orientation[3]

        self.pose_publisher.publish(message)
    
    def publish_target_pose(self):
        position, orientation = pb.getBasePositionAndOrientation(
            self.target_id
        )

        message = PoseStamped()

        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'world'

        message.pose.position.x = position[0]
        message.pose.position.y = position[1]
        message.pose.position.z = position[2]

        message.pose.orientation.x = orientation[0]
        message.pose.orientation.y = orientation[1]
        message.pose.orientation.z = orientation[2]
        message.pose.orientation.w = orientation[3]

        self.target_pose_publisher.publish(message)
    
    def publish_obstacle_pose(self):
        position, orientation = pb.getBasePositionAndOrientation(
            self.obstacle_id
        )

        message = PoseStamped()

        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = 'world'

        message.pose.position.x = position[0]
        message.pose.position.y = position[1]
        message.pose.position.z = position[2]

        message.pose.orientation.x = orientation[0]
        message.pose.orientation.y = orientation[1]
        message.pose.orientation.z = orientation[2]
        message.pose.orientation.w = orientation[3]

        self.obstacle_pose_publisher.publish(message)
    
    def reset_simulation_callback(self, request, response):
        del request

        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

        pb.resetBasePositionAndOrientation(
            self.robot_id,
            self.robot_start_position,
            self.robot_start_orientation,
        )

        pb.resetBaseVelocity(
            self.robot_id,
            linearVelocity=[0.0, 0.0, 0.0],
            angularVelocity=[0.0, 0.0, 0.0],
        )

        response.success = True
        response.message = 'Simulation reset successfully.'

        self.get_logger().info(response.message)

        return response

    def cmd_vel_callback(self, message):
        self.linear_velocity = message.linear.x
        self.angular_velocity = message.angular.z



def main(args=None):
    rclpy.init(args=args)
    node = PyBulletSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__=='__main__':
    main()