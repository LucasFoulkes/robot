# robot

Application-level ROS 2 Jazzy package for the Ackermann robot. It owns the
robot model, robot-wide configuration, and top-level launch descriptions while
reusing the hardware-, controller-, and odometry-specific packages.

## Included packages

- `rplidar_ros`: RPLIDAR C1 driver, publishing `/scan`
- `mola_lidar_odometry`: upstream MOLA 2D scan-to-map odometry (`odom -> base_link`)
- `ackermann_adaptive_controller`: learning Nav2 `/cmd_vel` to steering/throttle controller
- `pico_ackermann_driver`: USB serial transport and Pico actuator watchdog
- `dualshock4_bringup` / `dualshock4_teleop`: manual driving (teleop launch only)

The measured hardware model is installed from
`urdf/ackermann_robot.urdf.xacro`. The fixed `base_link -> laser` transform is
therefore owned by this package rather than duplicated in a sensor launch file.

## Build

Install the official MOLA ROS release from the ROS build farm; do not vendor or
fork it inside this package:

```bash
sudo apt update
sudo apt install \
  ros-jazzy-mola-lidar-odometry \
  ros-jazzy-mola-bridge-ros2
```

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select robot
source install/setup.bash
```

## Run

The whole autonomy stack -- LiDAR, MOLA odometry, Nav2 in the `odom` frame
(no map, no localization), the adaptive controller, the Pico driver:

```bash
ros2 launch robot robot.launch.py                    # controller armed
ros2 launch robot robot.launch.py start_active:=false use_rviz:=true
```

Send goals with RViz's "2D Goal Pose". Goals must land inside the rolling
24 m global costmap window. There is no obstacle layer: the operator is the
safety system, and the stop is

```bash
ros2 service call /ackermann_adaptive_controller/set_active std_srvs/srv/SetBool "{data: false}"
```

Manual driving only (joystick, axis mappers, Pico driver -- no LiDAR, no Nav2):

```bash
ros2 launch robot teleop.launch.py
```

The two are mutually exclusive: both write the actuator topics. Model and
MOLA odometry alone (the C1 driver must already publish `/scan`):

```bash
ros2 launch robot mola_lidar_odometry.launch.py
```

All launches accept `scan_topic:=/scan` and `use_sim_time:=false`.

The teleop configuration uses L1 as the deadman for both steering and
throttle. Steering uses the left stick horizontal axis at scale `0.6`.
Throttle uses the right stick vertical axis at scale `1.0`; SDL reports up as
negative, so that mapper is inverted to make stick-forward positive. Verify
the live axis and sign before connecting the motor battery.

The Pico driver stays at its normal `[-1.0, 1.0]` command limit. Unloaded
servo calibration remains a deliberate manual procedure outside this launch
file.
