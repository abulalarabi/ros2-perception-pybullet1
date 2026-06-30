#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_simulation',
            executable='simulator',
            name='pybullet_simulator',
            output='screen',
        ),

        Node(
            package='robot_perception',
            executable='target_detector',
            name='target_detector',
            output='screen',
        ),

        Node(
            package='robot_perception',
            executable='obstacle_detector',
            name='obstacle_detector',
            output='screen',
        ),

        Node(
            package='robot_control',
            executable='autonomous_controller',
            name='autonomous_controller',
            output='screen',
        ),

        Node(
            package='robot_control',
            executable='command_mux',
            name='command_mux',
            output='screen',
        ),

        Node(
            package='robot_manual_control',
            executable='mode_manager',
            name='mode_manager',
            output='screen',
        ),
    ])