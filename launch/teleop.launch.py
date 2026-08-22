# Copyright 2026 Lucas Foulkes
# Use of this source code is governed by an MIT-style license that can be found
# in the LICENSE file or at https://opensource.org/licenses/MIT.

"""Manual driving with the DualShock 4. Nothing else.

Deliberately minimal: joystick, the two axis mappers, and the Pico driver. No
LiDAR, no MOLA, no Nav2, no adaptive controller. That is the point -- it is the
smallest thing that can make the robot move, so if the machine still dies while
driving under this launch, the cause is the actuator power path and not the
autonomy stack.

Mutually exclusive with robot.launch.py: both write the same actuator topics.

L1 is the deadman for both channels. Left stick horizontal steers (scale 0.6),
right stick vertical drives (scale 1.0, inverted because SDL reports up as
negative).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Build the manual-driving launch description."""
    robot_share = get_package_share_directory('robot')
    dualshock_share = get_package_share_directory('dualshock4_bringup')
    config = LaunchConfiguration('config')

    return LaunchDescription([
        DeclareLaunchArgument(
            'config',
            default_value=os.path.join(robot_share, 'config', 'robot.yaml'),
            description='Path to the robot YAML configuration.'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                dualshock_share, 'launch', 'dualshock4.launch.py'))),

        Node(package='pico_ackermann_driver',
             executable='pico_ackermann_driver',
             name='pico_ackermann_driver',
             output='screen', parameters=[config]),

        Node(package='dualshock4_teleop', executable='joy_axis_mapper',
             name='joy_axis_mapper',
             output='screen', parameters=[config]),
        Node(package='dualshock4_teleop', executable='joy_axis_mapper',
             name='joy_axis_mapper_throttle',
             output='screen', parameters=[config]),
    ])
