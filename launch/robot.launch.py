# Copyright 2026 Lucas Foulkes
# Use of this source code is governed by an MIT-style license that can be found
# in the LICENSE file or at https://opensource.org/licenses/MIT.

"""Launch controller input, steering teleop, and the Pico driver."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Build the operational robot launch description."""
    robot_share = get_package_share_directory('robot')
    dualshock_share = get_package_share_directory('dualshock4_bringup')

    default_config = os.path.join(robot_share, 'config', 'robot.yaml')
    dualshock_launch = os.path.join(
        dualshock_share,
        'launch',
        'dualshock4.launch.py',
    )
    config = LaunchConfiguration('config')

    return LaunchDescription([
        DeclareLaunchArgument(
            'config',
            default_value=default_config,
            description='Path to the robot YAML configuration.',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(dualshock_launch),
        ),
        Node(
            package='pico_ackermann_driver',
            executable='pico_ackermann_driver',
            name='pico_ackermann_driver',
            output='screen',
            parameters=[config],
        ),
        Node(
            package='dualshock4_teleop',
            executable='joy_axis_mapper',
            name='joy_axis_mapper',
            output='screen',
            parameters=[config],
        ),
    ])
