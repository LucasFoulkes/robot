# Copyright 2026 Lucas Foulkes
# Use of this source code is governed by an MIT-style license that can be found
# in the LICENSE file or at https://opensource.org/licenses/MIT.

"""Launch the packaged robot model and upstream MOLA 2D LiDAR odometry."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Build the model and MOLA-only launch description."""
    scan_topic = LaunchConfiguration('scan_topic')
    use_sim_time = LaunchConfiguration('use_sim_time')

    model = PathJoinSubstitution([
        FindPackageShare('robot'),
        'urdf',
        'ackermann_robot.urdf.xacro',
    ])
    upstream_mola_launch = PathJoinSubstitution([
        FindPackageShare('mola_lidar_odometry'),
        'ros2-launchs',
        'ros2-lidar-odometry.launch.py',
    ])

    robot_description = ParameterValue(
        Command(['xacro ', model]),
        value_type=str,
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'scan_topic',
            default_value='/scan',
            description='LaserScan topic produced by the C1 driver.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time.',
        ),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': use_sim_time,
            }],
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(upstream_mola_launch),
            launch_arguments={
                'lidar_topic_name': scan_topic,
                'lidar_topic_type': 'LaserScan',
                'lidar_qos_reliability': 'best_effort',
                'lidar_qos_depth': '20',
                'lidar_scan_validity_minimum_point_count': '100',
                'mola_tf_base_link': 'base_link',
                'ignore_lidar_pose_from_tf': 'False',
                'mola_lo_pipeline': '../pipelines/lidar2d.yaml',
                'enforce_planar_motion': 'True',
                'mola_deskew_method': 'MotionCompensationMethod::Linear',
                'mola_lo_reference_frame': 'odom',
                'publish_localization_following_rep105': 'False',
                'use_state_estimator': 'False',
                'start_active': 'True',
                'start_mapping_enabled': 'True',
                'generate_simplemap': 'False',
                'use_mola_gui': 'False',
                'use_rviz': 'False',
                'use_diagnostic_aggregator': 'False',
                'use_sim_time': use_sim_time,
            }.items(),
        ),
    ])
