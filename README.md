# ROS 2 Perception, Control, and Manual Intervention with PyBullet

This project is a more complete ROS 2 practice example that combines simulation, perception, autonomous control, manual control, and command arbitration.

The robot runs inside PyBullet and tries to detect and approach a target while monitoring an obstacle. A human operator can switch between autonomous and manual modes, pause the robot, or trigger an emergency stop.

The main goal of this project is to understand how multiple ROS 2 packages and nodes work together in a realistic robotics pipeline.

---

## Problem Statement

Build a simulated mobile robot that can:

* detect a target object,
* estimate the target position relative to the robot,
* detect nearby obstacles,
* search for and approach the target autonomously,
* accept manual keyboard commands,
* switch between manual and autonomous control,
* pause the robot,
* trigger an emergency stop,
* reset the simulation.

The robot operates in a PyBullet world containing:

* a blue mobile robot,
* a red target object,
* a gray obstacle,
* a ground plane.

The autonomous controller uses a simple state machine:

```text
SEARCH
  ↓
ALIGN
  ↓
APPROACH
  ↓
STOP
```

If the target is not visible, the robot rotates to search for it.

If the target is visible but not centered, the robot rotates to align with it.

Once aligned, the robot moves toward the target and stops at a specified distance.

The current obstacle logic stops the robot when an obstacle is too close. Reactive obstacle avoidance can be added later.

Manual control always remains available through the control-mode system.

---

# ROS 2 Workflow Used in This Project

This section briefly summarizes the main ROS 2 commands used to create and build the project.

## Create a workspace

```bash
mkdir -p ~/Desktop/ros2_perception_control_ws/src
cd ~/Desktop/ros2_perception_control_ws/src
```

## Create a CMake package

Used for custom messages, services, actions, and launch-only packages:

```bash
ros2 pkg create robot_interfaces \
  --build-type ament_cmake
```

## Create a Python package

Used for ROS 2 Python nodes:

```bash
ros2 pkg create robot_simulation \
  --build-type ament_python \
  --dependencies rclpy geometry_msgs robot_interfaces
```

## Build the workspace

```bash
cd ~/Desktop/ros2_perception_control_ws

colcon build --symlink-install
```

For this setup, the virtual-environment Python was explicitly used when needed:

```bash
colcon build \
  --symlink-install \
  --cmake-args \
  -DPython3_EXECUTABLE="$VIRTUAL_ENV/bin/python3"
```

## Source the workspace

```bash
source /opt/ros/lyrical/setup.bash
source ~/Desktop/ros2_perception_control_ws/install/setup.bash
```

## Run a node

```bash
ros2 run <package_name> <executable_name>
```

Example:

```bash
ros2 run robot_simulation simulator
```

## Run a launch file

```bash
ros2 launch robot_bringup full_system.launch.py
```

## Inspect the ROS graph

```bash
ros2 node list
ros2 topic list
ros2 service list
ros2 action list
```

## Inspect a node

```bash
ros2 node info /pybullet_simulator
```

## Read a topic

```bash
ros2 topic echo /robot/pose
```

## Call a service

```bash
ros2 service call \
  /set_control_mode \
  robot_interfaces/srv/SetControlMode \
  "{mode: 1}"
```

---

# Project Structure

```text
ros2_perception_control_ws/
├── src/
│   ├── robot_interfaces/
│   │   ├── msg/
│   │   │   ├── TargetDetection.msg
│   │   │   ├── ObstacleInfo.msg
│   │   │   └── ControlMode.msg
│   │   ├── srv/
│   │   │   ├── SetControlMode.srv
│   │   │   └── ResetSimulation.srv
│   │   ├── action/
│   │   │   └── ApproachTarget.action
│   │   ├── CMakeLists.txt
│   │   └── package.xml
│   │
│   ├── robot_simulation/
│   │   ├── robot_simulation/
│   │   │   ├── __init__.py
│   │   │   └── pybullet_simulator.py
│   │   ├── setup.py
│   │   ├── setup.cfg
│   │   └── package.xml
│   │
│   ├── robot_perception/
│   │   ├── robot_perception/
│   │   │   ├── __init__.py
│   │   │   ├── target_detector.py
│   │   │   └── obstacle_detector.py
│   │   ├── setup.py
│   │   ├── setup.cfg
│   │   └── package.xml
│   │
│   ├── robot_control/
│   │   ├── robot_control/
│   │   │   ├── __init__.py
│   │   │   ├── autonomous_controller.py
│   │   │   └── command_mux.py
│   │   ├── setup.py
│   │   ├── setup.cfg
│   │   └── package.xml
│   │
│   ├── robot_manual_control/
│   │   ├── robot_manual_control/
│   │   │   ├── __init__.py
│   │   │   ├── keyboard_teleop.py
│   │   │   └── mode_manager.py
│   │   ├── setup.py
│   │   ├── setup.cfg
│   │   └── package.xml
│   │
│   └── robot_bringup/
│       ├── launch/
│       │   └── full_system.launch.py
│       ├── CMakeLists.txt
│       └── package.xml
│
├── build/
├── install/
└── log/
```

---

# Package Overview

## `robot_interfaces`

Contains the custom ROS 2 interfaces shared across the project.

### Messages

```text
TargetDetection.msg
ObstacleInfo.msg
ControlMode.msg
```

### Services

```text
SetControlMode.srv
ResetSimulation.srv
```

### Action

```text
ApproachTarget.action
```

This package uses `ament_cmake` because ROS 2 custom interfaces are generated using `rosidl_generate_interfaces()`.

---

## `robot_simulation`

Contains the PyBullet simulation.

The simulator:

* creates the robot,
* creates the target,
* creates the obstacle,
* advances the physics simulation,
* receives velocity commands,
* publishes robot pose,
* publishes target and obstacle ground-truth poses,
* provides a reset service.

Main node:

```text
/pybullet_simulator
```

Main executable:

```bash
ros2 run robot_simulation simulator
```

---

## `robot_perception`

Contains the target and obstacle perception nodes.

### Target detector

Subscribes to:

```text
/robot/pose
/simulation/target_pose
```

Publishes:

```text
/perception/target
```

The detector calculates:

* relative target position,
* target distance,
* target bearing,
* visibility based on field of view,
* detection confidence.

### Obstacle detector

Subscribes to:

```text
/robot/pose
/simulation/obstacle_pose
```

Publishes:

```text
/perception/obstacle
```

The detector calculates:

* obstacle distance,
* obstacle bearing,
* obstacle position in the robot frame,
* whether the obstacle is inside the detection range.

---

## `robot_control`

Contains autonomous control and command arbitration.

### Autonomous controller

Subscribes to:

```text
/perception/target
/perception/obstacle
```

Publishes:

```text
/cmd_vel/autonomous
```

The controller uses these states:

```text
SEARCH
ALIGN
APPROACH
STOP
OBSTACLE_STOP
```

Current obstacle behavior is intentionally simple. The robot stops when an obstacle is too close.

### Command mux

Subscribes to:

```text
/cmd_vel/autonomous
/cmd_vel/manual
/control_mode
```

Publishes:

```text
/cmd_vel
```

The command mux decides which command reaches the simulator.

```text
MANUAL
  → use /cmd_vel/manual

AUTONOMOUS
  → use /cmd_vel/autonomous

PAUSED
  → publish zero velocity

EMERGENCY_STOP
  → publish zero velocity
```

---

## `robot_manual_control`

Contains manual control and mode management.

### Keyboard teleop

Publishes manual velocity commands on:

```text
/cmd_vel/manual
```

Keyboard controls:

```text
w      move forward
s      move backward
a      turn left
d      turn right
space  stop
q      quit
```

Run it with:

```bash
ros2 run robot_manual_control keyboard_teleop
```

### Mode manager

Publishes:

```text
/control_mode
```

Provides:

```text
/set_control_mode
```

Supported modes:

```text
0 = MANUAL
1 = AUTONOMOUS
2 = PAUSED
3 = EMERGENCY_STOP
```

The system starts in manual mode.

---

## `robot_bringup`

Contains the launch file for starting the full system.

Run:

```bash
ros2 launch robot_bringup full_system.launch.py
```

This starts:

* PyBullet simulator,
* target detector,
* obstacle detector,
* autonomous controller,
* command mux,
* mode manager.

The keyboard teleop node is not included in the launch file because it needs direct access to an interactive terminal.

---

# Communication Flow

```text
PyBullet Simulator
        |
        | /robot/pose
        | /simulation/target_pose
        | /simulation/obstacle_pose
        v
Perception Nodes
        |
        | /perception/target
        | /perception/obstacle
        v
Autonomous Controller
        |
        | /cmd_vel/autonomous
        v
Command Mux <--------- /cmd_vel/manual
        |
        | /cmd_vel
        v
PyBullet Simulator
```

The mode manager also controls the command mux through:

```text
/control_mode
```

---

# Requirements

This project was developed with:

* ROS 2 Lyrical
* Python 3.14
* PyBullet
* Ubuntu Linux
* `colcon`
* `rclpy`

---

# Python Environment

A virtual environment created from the system Python was used so that PyBullet could be installed without modifying the system Python packages.

Create the environment:

```bash
/usr/bin/python3 -m venv \
  ~/venvs/ros2-lyrical \
  --system-site-packages
```

Activate it:

```bash
source ~/venvs/ros2-lyrical/bin/activate
```

Install PyBullet:

```bash
python -m pip install pybullet
```

Check the main imports:

```bash
python -c "
import rclpy
import pybullet

print('rclpy OK')
print('PyBullet OK')
"
```

---

# Build Instructions

Activate the environment:

```bash
source ~/venvs/ros2-lyrical/bin/activate
```

Source ROS 2:

```bash
source /opt/ros/lyrical/setup.bash
```

Go to the workspace:

```bash
cd ~/Desktop/ros2_perception_control_ws
```

Build:

```bash
colcon build \
  --symlink-install \
  --cmake-args \
  -DPython3_EXECUTABLE="$VIRTUAL_ENV/bin/python3"
```

Source the workspace:

```bash
source install/setup.bash
```

---

# Run the Full System

```bash
ros2 launch robot_bringup full_system.launch.py
```

The PyBullet window should open with:

* a blue robot,
* a red target,
* a gray obstacle,
* a ground plane.

---

# Switch Control Modes

## Manual mode

```bash
ros2 service call \
  /set_control_mode \
  robot_interfaces/srv/SetControlMode \
  "{mode: 0}"
```

Then run:

```bash
ros2 run robot_manual_control keyboard_teleop
```

## Autonomous mode

```bash
ros2 service call \
  /set_control_mode \
  robot_interfaces/srv/SetControlMode \
  "{mode: 1}"
```

## Paused mode

```bash
ros2 service call \
  /set_control_mode \
  robot_interfaces/srv/SetControlMode \
  "{mode: 2}"
```

## Emergency stop

```bash
ros2 service call \
  /set_control_mode \
  robot_interfaces/srv/SetControlMode \
  "{mode: 3}"
```

---

# Reset the Simulation

```bash
ros2 service call \
  /reset_simulation \
  robot_interfaces/srv/ResetSimulation \
  "{}"
```

---

# Useful Inspection Commands

Check the robot pose:

```bash
ros2 topic echo /robot/pose
```

Check target perception:

```bash
ros2 topic echo /perception/target
```

Check obstacle perception:

```bash
ros2 topic echo /perception/obstacle
```

Check the current mode:

```bash
ros2 topic echo /control_mode
```

Check the final velocity command:

```bash
ros2 topic echo /cmd_vel
```

List running nodes:

```bash
ros2 node list
```

Inspect the command mux:

```bash
ros2 node info /command_mux
```

---

# Current Limitations

The project is intentionally simple and focuses on ROS 2 communication and architecture.

Current limitations include:

* perception uses ground-truth object poses instead of camera images,
* only one target and one obstacle are simulated,
* obstacle handling currently stops the robot instead of avoiding the obstacle,
* the mobile robot is a simple PyBullet box,
* no URDF model is used,
* no TF tree is published,
* the custom action interface is defined but not yet fully integrated into the autonomous controller.

---

# Possible Next Steps

Some useful improvements would be:

* add reactive obstacle avoidance,
* integrate the `ApproachTarget` action,
* add action cancellation,
* use PyBullet camera images for target detection,
* simulate lidar or range sensors,
* add multiple obstacles,
* add a URDF-based robot,
* publish TF frames,
* visualize the system in RViz,
* add ROS 2 parameters and YAML configuration,
* add watchdog timeouts for stale commands,
* add automated tests,
* add a behavior tree or planner.

---

# What I Learned

This project helped me practice:

* creating ROS 2 workspaces,
* creating `ament_python` and `ament_cmake` packages,
* defining custom messages, services, and actions,
* building packages with `colcon`,
* sourcing ROS 2 workspaces,
* creating publishers and subscribers,
* creating services,
* creating launch files,
* building a simple perception pipeline,
* implementing an autonomous state machine,
* creating keyboard teleoperation,
* switching between manual and autonomous control,
* using a command mux,
* integrating ROS 2 with PyBullet.

---

# License

This project is available under the Apache 2.0 License.
