
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, SetEnvironmentVariable, 
                            IncludeLaunchDescription, SetLaunchConfiguration)
from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from launch.actions import TimerAction
from launch.actions import ExecuteProcess



def generate_launch_description():
    gz_share = get_package_share_directory('ros_gz_sim')
    pkg_share = get_package_share_directory('rover_sim')

    default_world = PathJoinSubstitution([pkg_share, "sdf", "diff_drive.sdf"])
    # default_world = PathJoinSubstitution([pkg_share, "sdf", "rover.sdf"])


    # Set Ignition environment variables for debugging
    ign_resource_path = SetEnvironmentVariable(
        'IGN_GAZEBO_RESOURCE_PATH', 
        TextSubstitution(text=os.path.join(pkg_share, 'models'))
    )

    ign_system_plugin_path = SetEnvironmentVariable(
        'IGN_GAZEBO_SYSTEM_PLUGIN_PATH',
        TextSubstitution(text='/usr/lib/x86_64-linux-gnu/ign-gazebo-6/plugins')
    )

    ign_debug = DeclareLaunchArgument(
        'ign_debug',
        default_value='4',  # Verbose level 4
        description='Set Ignition Gazebo verbosity level'
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([gz_share, 'launch', 'gz_sim.launch.py'])),
        launch_arguments=[
            ("gz_args", [default_world, " -r -v "])  # -r (run), -v 4 (verbose)
        ]
    )

    bridge_config = PathJoinSubstitution([pkg_share, "config", "bridge_config.yaml"])
    
    ros_ign_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{"config_file": bridge_config}],
        output="screen"
    )
    madgwick_ndoe=Node(
            package='imu_filter_madgwick',
            executable='imu_filter_madgwick_node',
            name='imu_filter',
            output='screen',
            parameters=[
                {'use_mag': True},
                {'gain': 0.001},
                {'publish_tf': True},
                {'fixed_frame': 'odom'}
            ],
            remappings=[
                ('imu/data_raw', '/imu/data'),
                ('imu/mag', '/mag/raw'),
                ('imu/data', '/imu/filter')
            ]
        )

    sim_odom = TimerAction(
        period=1.0,  # Delay node start by 5 seconds
        actions=[
            Node(
                package='rover_sim',
                executable='ign_rover_odom.py',
                name='odom_ign',
                
                output='screen',
            )
        ]
    )
    # delayed_sim_odom = TimerAction(
    #     period=5.0,
    #     actions=[
    #         ExecuteProcess(
    #             cmd=['ros2', 'run', 'rover_sim', 'ign_rover_odom.py'],
    #             name='go_goal_ign',
    #             output='screen'
    #         )
    #     ]
    # )



    return LaunchDescription([
        
        gazebo,
        
        ros_ign_bridge,
        sim_odom,
        madgwick_ndoe,
    
        # sim_odom
    ])