# Copyright 2026 Lucas Foulkes
# Use of this source code is governed by an MIT-style license that can be found
# in the LICENSE file or at https://opensource.org/licenses/MIT.

"""The whole robot: LiDAR, odometry, Nav2 in the odom frame, actuators.

One command brings up everything needed to drive by dropping a Nav2 goal in
RViz. There is no joystick and no teleop path: the adaptive controller is the
only thing writing to the actuator topics.

There is therefore also no hardware e-stop. The stop is:

    ros2 service call /ackermann_adaptive_controller/set_active \\
        std_srvs/srv/SetBool "{data: false}"

The controller ARMS ITSELF at launch: ``start_active: true`` in
config/robot.yaml, overridable with ``start_active:=false``. That is safe on
its own -- Nav2 emits no cmd_vel until a goal is accepted -- so the robot sits
still until you send one. The override goes through the same RewrittenYaml
pass as ``odom_topic``.

Why the two includes below are wrapped in scoped GroupActions: launch
configurations are global to the context unless a group scopes them, and the
upstream MOLA launch declares arguments named ``start_active`` and
``use_rviz`` too. Passing it ``start_active: True`` overwrote this file's
``start_active:=false`` before the controller's parameters were evaluated --
which is what once made the rewrite look like it "silently did nothing" --
and its ``use_rviz: False`` switched RViz off the same way. With
``scoped=True`` the include's configurations die with the include.

Navigation is odom-relative. There is no map and no localization, so goals are
only reachable inside the rolling global costmap window (24 m square, see
config/nav2_params.yaml) and the frame drifts over long runs.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction,
                            IncludeLaunchDescription)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from nav2_common.launch import RewrittenYaml


LIFECYCLE_NODES = [
    'controller_server',
    'planner_server',
    'behavior_server',
    'bt_navigator',
    'velocity_smoother',
]

TF_REMAP = [('/tf', 'tf'), ('/tf_static', 'tf_static')]


def generate_launch_description():
    """Build the full robot launch description."""
    robot_share = get_package_share_directory('robot')
    rplidar_share = get_package_share_directory('rplidar_ros')

    config = LaunchConfiguration('config')
    nav2_params = LaunchConfiguration('nav2_params')
    scan_topic = LaunchConfiguration('scan_topic')
    odom_topic = LaunchConfiguration('odom_topic')
    start_active = LaunchConfiguration('start_active')
    use_sim_time = LaunchConfiguration('use_sim_time')
    sim_time_bool = ParameterValue(use_sim_time, value_type=bool)
    autostart = LaunchConfiguration('autostart')
    start_lidar = LaunchConfiguration('start_lidar')
    lidar_port = LaunchConfiguration('lidar_port')
    use_rviz = LaunchConfiguration('use_rviz')

    bt_dir = os.path.join(robot_share, 'behavior_trees')
    default_bt = os.path.join(bt_dir, 'navigate_to_pose_ackermann.xml')
    default_bt_poses = os.path.join(
        bt_dir, 'navigate_through_poses_ackermann.xml')

    robot_config = RewrittenYaml(
        source_file=config,
        root_key='',
        param_rewrites={'odom_topic': odom_topic,
                        'start_active': start_active,
                        'use_sim_time': use_sim_time},
        convert_types=True,
    )

    nav2_config = RewrittenYaml(
        source_file=nav2_params,
        root_key='',
        param_rewrites={
            'use_sim_time': use_sim_time,
            'default_nav_to_pose_bt_xml': default_bt,
            'default_nav_through_poses_bt_xml': default_bt_poses,
        },
        convert_types=True,
    )

    def nav2(package, executable, name, extra_remaps=()):
        return Node(package=package, executable=executable, name=name,
                    output='screen', parameters=[nav2_config],
                    remappings=TF_REMAP + list(extra_remaps))

    return LaunchDescription([
        DeclareLaunchArgument(
            'config',
            default_value=os.path.join(robot_share, 'config', 'robot.yaml'),
            description='Path to the robot YAML configuration.'),
        DeclareLaunchArgument(
            'nav2_params',
            default_value=os.path.join(
                robot_share, 'config', 'nav2_params.yaml'),
            description='Path to the Nav2 YAML configuration.'),
        DeclareLaunchArgument(
            'scan_topic', default_value='/scan',
            description='LaserScan topic consumed by MOLA and the costmaps.'),
        DeclareLaunchArgument(
            'odom_topic', default_value='/lidar_odometry/pose',
            description='nav_msgs/Odometry topic published by MOLA.'),
        DeclareLaunchArgument(
            'start_active', default_value='true',
            description='Arm the adaptive controller at launch. false '
                        'comes up PASSIVE (learning, publishing nothing).'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use simulation time.'),
        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Automatically configure and activate Nav2.'),
        DeclareLaunchArgument(
            'start_lidar', default_value='true',
            description='Start the RPLIDAR C1 driver.'),
        DeclareLaunchArgument(
            'lidar_port', default_value='/dev/ttyUSB0',
            description='RPLIDAR C1 serial port.'),
        DeclareLaunchArgument(
            'use_rviz', default_value='false',
            description='Start RViz with the odom-frame Nav2 view.'),

        # -- sensing -------------------------------------------------------
        GroupAction([IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                rplidar_share, 'launch', 'rplidar_c1_launch.py')),
            condition=IfCondition(start_lidar),
            launch_arguments={'serial_port': lidar_port,
                              'frame_id': 'laser'}.items()),
        ], scoped=True, forwarding=True),

        # -- model and odometry --------------------------------------------
        # Scoped: see the module docstring. MOLA's own start_active/use_rviz
        # launch arguments must not leak into this file's.
        GroupAction([IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                robot_share, 'launch', 'mola_lidar_odometry.launch.py')),
            # MOLA gets the RAW scan. Nothing in this stack consumes a
            # filtered one any more (no obstacle layer, no collision
            # monitor); the antenna's fixed return is a rigid point in the
            # body frame, which ICP handles. Feeding MOLA a filtered scan
            # once stopped it emitting odometry entirely. The measured
            # self-filter polygon is kept in docs/scan_filter.yaml for when
            # an obstacle layer comes back.
            launch_arguments={'scan_topic': scan_topic,
                              'use_sim_time': use_sim_time}.items()),
        ], scoped=True, forwarding=True),

        # -- actuators -----------------------------------------------------
        Node(package='pico_ackermann_driver',
             executable='pico_ackermann_driver',
             name='pico_ackermann_driver',
             output='screen', parameters=[config]),

        # -- the Twist -> actuator shim ------------------------------------
        Node(package='ackermann_adaptive_controller',
             executable='ackermann_adaptive_controller',
             name='ackermann_adaptive_controller',
             output='screen',
             parameters=[robot_config]),

        # -- Nav2 ----------------------------------------------------------
        GroupAction([
            nav2('nav2_controller', 'controller_server', 'controller_server',
                 [('cmd_vel', 'cmd_vel_nav')]),
            # No smoother_server: Smac Hybrid smooths its own paths.
            nav2('nav2_planner', 'planner_server', 'planner_server'),
            nav2('nav2_behaviors', 'behavior_server', 'behavior_server',
                 [('cmd_vel', 'cmd_vel_nav')]),
            nav2('nav2_bt_navigator', 'bt_navigator', 'bt_navigator'),
            # The smoother's output goes straight to the adaptive
            # controller: no collision monitor in between, by choice.
            nav2('nav2_velocity_smoother', 'velocity_smoother',
                 'velocity_smoother', [('cmd_vel', 'cmd_vel_nav'),
                                       ('cmd_vel_smoothed', 'cmd_vel')]),
            Node(package='nav2_lifecycle_manager',
                 executable='lifecycle_manager',
                 name='lifecycle_manager_navigation', output='screen',
                 parameters=[{
                     'autostart': ParameterValue(autostart, value_type=bool),
                     'node_names': LIFECYCLE_NODES,
                     'use_sim_time': sim_time_bool}]),
        ]),

        # -- operator view ---------------------------------------------------
        Node(package='rviz2', executable='rviz2', name='rviz2',
             condition=IfCondition(use_rviz),
             arguments=['-d', os.path.join(
                 robot_share, 'rviz', 'odom_nav.rviz')],
             output='screen', remappings=TF_REMAP),
    ])
