# robot

Application-level ROS 2 Jazzy package for the Ackermann robot. It owns robot
nodes, robot-wide configuration, and the top-level launch description while
reusing the hardware- and controller-specific packages.

## Included packages

- `dualshock4_bringup`: Bluetooth connection and `/joy` publication
- `dualshock4_teleop`: joystick axis to normalized steering command
- `pico_ackermann_driver`: USB serial transport and Pico actuator watchdog

## Build

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select robot
source install/setup.bash
```

## Run

```bash
ros2 launch robot robot.launch.py
```

The operational configuration keeps L1 as the steering deadman and keeps the
Pico driver at its normal `[-1.0, 1.0]` command limit. Unloaded servo
calibration remains a deliberate manual procedure outside this launch file.
