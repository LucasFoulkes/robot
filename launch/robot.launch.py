# Copyright 2026 Lucas Foulkes
# Use of this source code is governed by an MIT-style license that can be found
# in the LICENSE file or at https://opensource.org/licenses/MIT.

"""Launch the robot model, MOLA odometry, teleop, and Pico driver."""

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
    mola_launch = os.path.join(
        robot_share,
        'launch',
        'mola_lidar_odometry.launch.py',
    )
    dualshock_launch = os.path.join(
        dualshock_share,
        'launch',
        'dualshock4.launch.py',
    )
    config = LaunchConfiguration('config')
    scan_topic = LaunchConfiguration('scan_topic')
    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'config',
            default_value=default_config,
            description='Path to the robot YAML configuration.',
        ),
        DeclareLaunchArgument(
            'scan_topic',
            default_value='/scan',
            description='LaserScan topic consumed by MOLA.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time for the model and MOLA.',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(mola_launch),
            launch_arguments={
                'scan_topic': scan_topic,
                'use_sim_time': use_sim_time,
            }.items(),
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
        Node(
            package='dualshock4_teleop',
            executable='joy_axis_mapper',
            name='joy_axis_mapper_throttle',
            output='screen',
            parameters=[config],
        ),
    ])
