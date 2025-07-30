# Rover Simulation Quick Guide

This repository contains a mobile manipulator rover simulation with Ignition Gazebo and ROS 2 Navigation.

## Setup

```bash
# Clone the repository
git clone https://github.com/Prathmesh2931/mobile_manipulator_ign_nav.git
cd mobile_manipulator_ign_nav

# Build the package
mkdir -p ~/ros2_ws/src
cp -r . ~/ros2_ws/src/
cd ~/ros2_ws
colcon build --packages-select rover_sim
source install/setup.bash
```

## Run Options

### Basic Rover in TurtleBot Arena
```bash
ros2 launch rover_sim turtle_rover_sim.launch.py
```
- Launches rover in TurtleBot arena world
- Control with: `ros2 run teleop_twist_keyboard teleop_twist_keyboard`

### Rover with Navigation
```bash
ros2 launch rover_sim rover_nav_bringup.launch.py
```
- Starts rover + Nav2 stack + RViz
- Set initial pose and goals in RViz

### Rover with 5-DOF Arm
```bash
ros2 launch rover_sim rover_arm.launch.py
```
- Launches rover with mounted arm
- Control arm: `ros2 run rover_sim control_arm.py demo`

## Key Topics
- Movement: `/cmd_vel` (Twist)
- Sensors: `/scan` (LaserScan), `/imu` (Imu)
- Arm joints: `/cmd_pos_joint1` to `/cmd_pos_joint6` (Float64)

## Troubleshooting
- Check TF frames: `ros2 run tf2_tools view_frames`
- Verify topics: `ros2 topic list | grep <topic_name>`