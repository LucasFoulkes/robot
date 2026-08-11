# robot

Application-level ROS 2 Jazzy package for the Ackermann robot. It owns the
robot model, robot-wide configuration, and top-level launch descriptions while
reusing the hardware-, controller-, and odometry-specific packages.

## Included packages

- `dualshock4_bringup`: Bluetooth connection and `/joy` publication
- `dualshock4_teleop`: joystick axes to normalized steering/throttle commands
- `mola_lidar_odometry`: upstream MOLA 2D scan-to-map odometry
- `pico_ackermann_driver`: USB serial transport and Pico actuator watchdog

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

Start only the model and MOLA odometry (the C1 driver must already publish
`/scan`):

```bash
ros2 launch robot mola_lidar_odometry.launch.py
```

Start model, MOLA, DualShock input/teleop, and the Pico driver:

```bash
ros2 launch robot robot.launch.py
```

Both launches accept `scan_topic:=/scan` and `use_sim_time:=false`.

The operational configuration uses L1 as the deadman for both steering and
throttle. Steering uses the left stick horizontal axis at scale `0.6`.
Throttle uses the right stick vertical axis at scale `1.0`; SDL reports up as
negative, so that mapper is inverted to make stick-forward positive. Verify
the live axis and sign before connecting the motor battery.

The Pico driver stays at its normal `[-1.0, 1.0]` command limit. Unloaded
servo calibration remains a deliberate manual procedure outside this launch
file.
