from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, SetEnvironmentVariable, 
                           IncludeLaunchDescription, ExecuteProcess)
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from launch.actions import TimerAction

def generate_launch_description():
    # Get package directories
    pkg_share = get_package_share_directory('rover_sim')
    turtlebot_share = get_package_share_directory('turtlebot3')
    
    # Try to get ros_gz_sim first, then fall back to ros_ign_gazebo
    try:
        gz_sim_share = get_package_share_directory('ros_gz_sim')
        spawn_pkg = 'ros_gz_gazebo'
        bridge_pkg = 'ros_gz_bridge'
        sim_launch = 'gz_sim.launch.py'
        print("Using ros_gz packages")
    except:
        gz_sim_share = get_package_share_directory('ros_ign_gazebo')
        spawn_pkg = 'ros_ign_gazebo'
        bridge_pkg = 'ros_ign_bridge'
        sim_launch = 'ign_gazebo.launch.py'
        print("Using ros_ign packages")
    
    # Load URDF file - Make sure this is the same URDF used in both setups
    urdf_file = os.path.join(pkg_share, 'urdf', 'waffle_4wheel.urdf')
    with open(urdf_file, 'r') as infp:
        robot_description = infp.read()
    
    # Set Ignition environment variables
    ign_resource_path = SetEnvironmentVariable(
        'IGN_GAZEBO_RESOURCE_PATH', 
        TextSubstitution(text=os.path.join(pkg_share, 'models') + ":" + 
                         os.path.join(pkg_share, 'sdf') + ":" +
                         os.path.join(pkg_share, 'worlds') + ":" +  
                         os.path.join(turtlebot_share, 'models'))
    )

    ign_system_plugin_path = SetEnvironmentVariable(
        'IGN_GAZEBO_SYSTEM_PLUGIN_PATH',
        TextSubstitution(text='/usr/lib/x86_64-linux-gnu/ign-gazebo-6/plugins')
    )

    # Use the exact same bridge configuration as your working example
    # Just add arm-specific topics
    ros_bridge = Node(
        package=bridge_pkg,
        executable='parameter_bridge',
        parameters=[{'use_sim_time': True}],
        arguments=[
            # Velocity command (ROS2 -> IGN)
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            # Odometry (IGN -> ROS2)
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            # TF (IGN -> ROS2) - IMPORTANT: Keep exactly as in working example
            '/odom/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            # Clock (IGN -> ROS2)
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            # Joint states (IGN -> ROS2)
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
            # Lidar (IGN -> ROS2) - use both paths to ensure compatibility
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            # '/model/rover_with_arm/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',

           
            '/scan/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked',
            # IMU (IGN -> ROS2) - use both paths to ensure compatibility
            '/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU',
            # '/model/rover_with_arm/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU',
            # Camera (IGN -> ROS2)
            '/camera/rgb/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image',
            '/camera/rgb/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo',
            # Add arm control topics
            '/cmd_pos_joint1@std_msgs/msg/Float64]ignition.msgs.Double',
            '/cmd_pos_joint2@std_msgs/msg/Float64]ignition.msgs.Double',
            '/cmd_pos_joint3@std_msgs/msg/Float64]ignition.msgs.Double',
            '/cmd_pos_joint4@std_msgs/msg/Float64]ignition.msgs.Double',
            '/cmd_pos_joint5@std_msgs/msg/Float64]ignition.msgs.Double',
            '/cmd_pos_joint6@std_msgs/msg/Float64]ignition.msgs.Double',
            # Gripper control
            '/pickup_target_box/attach@std_msgs/msg/Bool]ignition.msgs.Boolean',
            '/pickup_target_box/detach@std_msgs/msg/Bool]ignition.msgs.Boolean',
            '/pickup_target_box/state@std_msgs/msg/Bool[ignition.msgs.Boolean',
        ],
        remappings=[
            ("/odom/tf", "tf"),
        ],
        output='screen'
    )

    # Spawn the TurtleBot world model - keep exactly the same
    ignition_spawn_world = Node(
        package='ros_ign_gazebo',
        executable='create',
        output='screen',
        arguments=['-file', PathJoinSubstitution([
                        get_package_share_directory('turtlebot3'),
                        "models", "worlds", "model.sdf"]),
                   '-allow_renaming', 'false'],
    )
    
    # Spawn your rover with arm - CRITICAL: Use the same entity name pattern
    ignition_spawn_entity = Node(
            package='ros_ign_gazebo',
            executable='create',
            output='screen',
            arguments=['-entity', 'waffle_4wheel',  # IMPORTANT: Use same name as working example
                    '-name', 'waffle_4wheel',       # This is critical for TF to work
                    '-file', PathJoinSubstitution([
                            get_package_share_directory('rover_sim'),
                            "models", "rover_with_arm_model.sdf"]),  # Still use your arm model
                    '-allow_renaming', 'true',
                    '-x', '-2.0',
                    '-y', '-0.5',
                    '-z', '0.01'],
            )
    
    # Spawn the pickup box
    ignition_spawn_box = Node(
            package='ros_ign_gazebo',
            executable='create',
            output='screen',
            arguments=['-entity', 'pickup_box',
                    '-name', 'pickup_box',
                    '-file', PathJoinSubstitution([
                            get_package_share_directory('rover_sim'),
                            "models", "pickup_box.sdf"]),
                    '-allow_renaming', 'true',
                    '-x', '0.4',
                    '-y', '0.0',
                    '-z', '0.1'],
            )
    
    # Robot state publisher with the URDF - keep exactly the same
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': True}]
    )
    
    # Use the exact same odom_to_foot.py script
    odom_to_base_footprint = Node(
        package='rover_sim',
        executable='odom_to_foot.py',
        name='odom_to_base_footprint_tf',
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    # Map to odom static transform - keep exactly the same
    map_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_tf',
        arguments=['--frame-id', 'map', 
                  '--child-frame-id', 'odom',
                  '--x', '0', '--y', '0', '--z', '0',
                  '--roll', '0', '--pitch', '0', '--yaw', '0']
    )
    
    # base_footprint to base_link transform - keep exactly the same
    footprint_to_base_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='footprint_to_base_tf',
        arguments=['--frame-id', 'base_footprint', 
                  '--child-frame-id', 'base_link',
                  '--x', '0', '--y', '0', '--z', '0.01',
                  '--roll', '0', '--pitch', '0', '--yaw', '0']
    )
    
    # IMU filter - keep exactly the same
    madgwick_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        name='imu_filter',
        output='screen',
        parameters=[
            {'use_mag': False},
            {'gain': 0.1},
            {'publish_tf': False},  # IMPORTANT: Set to false to avoid conflicting transforms
            {'world_frame': 'enu'},
            {'fixed_frame': 'base_link'},  # Changed from odom to base_link
            {'use_magnetic_field_msg': True},
            {'remove_gravity_vector': False},
            {'orientation_stddev': 0.01}
        ],
        remappings=[
            ('imu/data_raw', 'imu'),
            ('imu/data', 'imu/filtered')
        ]
    )

    # RViz configuration
    rviz_config = os.path.join(pkg_share, 'rviz', 'robot.rviz')
    if os.path.exists(rviz_config):
        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': True}],
            output='screen'
        )
    else:
        rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            parameters=[{'use_sim_time': True}],
            output='screen'
        )

    # For debugging - uncomment as needed
    list_topics_node = ExecuteProcess(
        cmd=['bash', '-c', 'sleep 10 && echo "Available topics:" && ros2 topic list'],
        output='screen'
    )

    tf_monitor = ExecuteProcess(
        cmd=['bash', '-c', 'sleep 12 && echo "TF Tree:" && ros2 run tf2_tools view_frames && echo "PDF created"'],
        output='screen'
    )
    
    scan_monitor = ExecuteProcess(
        cmd=['bash', '-c', 'sleep 13 && echo "Checking scan topics:" && ros2 topic list | grep scan'],
        output='screen'
    )
    
    world_only = os.path.join(get_package_share_directory('turtlebot3'), "models", "worlds", "world_only.sdf")

    # Create the launch description - keep exactly the same structure
    ld = LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument('gui', default_value='true'),
        
        ign_resource_path,
        ign_system_plugin_path,
        
        # Launch Gazebo with empty world - keep exactly the same
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [os.path.join(get_package_share_directory('ros_ign_gazebo'),
                              'launch', 'ign_gazebo.launch.py')]),
            launch_arguments=[('ign_args', [' -r -v 3 ' +
                              world_only
                             ])]),
        
        # Setup bridge before spawning models
        TimerAction(
            period=1.0,
            actions=[ros_bridge]
        ),
        
        # After Gazebo is running, spawn models with delay
        TimerAction(
            period=3.0,
            actions=[ignition_spawn_world]
        ),
        
        TimerAction(
            period=5.0,
            actions=[ignition_spawn_entity]
        ),
        
        # Spawn pickup box (additional for the arm setup)
        TimerAction(
            period=5.5,
            actions=[ignition_spawn_box]
        ),
        
        # Start robot_state_publisher, map->odom TF, and footprint->base_link TF
        # Keep exactly the same order and timing
        TimerAction(
            period=6.0,
            actions=[
                robot_state_publisher,
                map_static_tf,
                footprint_to_base_tf,
                odom_to_base_footprint
            ]
        ),
        
        # Start other nodes with delay
        TimerAction(
            period=7.0,
            actions=[madgwick_node]
        ),
        
        # Launch RViz after everything is set up
        # TimerAction(
        #     period=8.0,
        #     actions=[rviz_node]
        # ),
        
        # Debug tools - uncomment as needed
        # TimerAction(
        #     period=9.0,
        #     actions=[list_topics_node, tf_monitor, scan_monitor]
        # )
    ])
    
    return ld