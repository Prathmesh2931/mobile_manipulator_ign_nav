
# from ament_index_python.packages import get_package_share_directory
# from launch import LaunchDescription
# from launch.actions import (DeclareLaunchArgument, SetEnvironmentVariable, 
#                             IncludeLaunchDescription, SetLaunchConfiguration)
# from launch.substitutions import PathJoinSubstitution, LaunchConfiguration, TextSubstitution
# from launch_ros.actions import Node
# from launch.launch_description_sources import PythonLaunchDescriptionSource
# import os
# from launch.actions import TimerAction
# from launch.actions import ExecuteProcess


# def generate_launch_description():
#     # Get package share directory
#     # pkg_rover_sim = get_package_share_directory('rover_sim')

#     # # World path
#     # world_file = os.path.join(pkg_rover_sim, 'worlds', 'rover_world.sdf')

#     # # Launch Gazebo with the world file
#     # gazebo = ExecuteProcess(
#     #     cmd=['ign', 'gazebo', '-v', '4', world_file],
#     #     output='screen',
#     #     additional_env={
#     #         'GZ_SIM_RESOURCE_PATH': os.path.join(pkg_rover_sim, 'sdf') + ':/usr/share/ignition/ignition-gazebo6/models'
#     #     }
#     # )

#     # # ROS-GZ Bridge
#     # bridge_config = PathJoinSubstitution([pkg_rover_sim, "config", "ros_gz_bridge.yaml"])
    
#     # ros_ign_bridge = Node(
#     #     package='ros_gz_bridge',
#     #     executable='parameter_bridge',
#     #     parameters=[{"config_file": bridge_config}],
#     #     output="screen"
#     # )

#     # # IMU Filter Node
#     # imu_filter = Node(
#     #     package='imu_filter_madgwick',
#     #     executable='imu_filter_madgwick_node',
#     #     name='imu_filter',
#     #     output='screen',
#     #     parameters=[
#     #         {'use_mag': True},  # Enable magnetometer since /mag/raw is available
#     #         {'publish_tf': False},
#     #         {'world_frame': 'enu'},
#     #         {'imu_topic': '/imu/data_raw'}
#     #     ]
#     # )

#     # return LaunchDescription([
#     #     DeclareLaunchArgument('world', default_value=world_file, description='Path to world SDF file'),
#     #     gazebo,
#     #     ros_ign_bridge,
#     #     imu_filter
#     # ])
#     gz_share = get_package_share_directory('ros_gz_sim')
#     pkg_share = get_package_share_directory('rover_sim')

#     default_world = PathJoinSubstitution([pkg_share, "sdf", "test_ign.urdf.xml"])

#     gazebo = IncludeLaunchDescription(
#         PythonLaunchDescriptionSource(PathJoinSubstitution([gz_share, 'launch', 'gz_sim.launch.py'])),
#         launch_arguments=[
#             ("gz_args", [default_world, " -r -v "])  # -r (run), -v 4 (verbose)
#         ]
#     )

#     bridge_config = PathJoinSubstitution([pkg_share, "config", "ros_gz_bridge.yaml"])
    
#     ros_ign_bridge = Node(
#         package='ros_gz_bridge',
#         executable='parameter_bridge',
#         parameters=[{"config_file": bridge_config}],
#         output="screen"
#     )
#     madgwick_ndoe=Node(
#             package='imu_filter_madgwick',
#             executable='imu_filter_madgwick_node',
#             name='imu_filter',
#             output='screen',
#             parameters=[
#                 {'use_mag': True},
#                 {'gain': 0.001},
#                 {'publish_tf': True},
#                 {'fixed_frame': 'odom'}
#             ],
#             remappings=[
#                 ('imu/data_raw', '/imu/data'),
#                 ('imu/mag', '/mag/raw'),
#                 ('imu/data', '/imu/filter')
#             ]
#         )

#     sim_odom = TimerAction(
#         period=1.0,  # Delay node start by 5 seconds
#         actions=[
#             Node(
#                 package='rover_sim',
#                 executable='ign_rover_odom.py',
#                 name='odom_ign',
                
#                 output='screen',
#             )
#         ]
#     )
#     # delayed_sim_odom = TimerAction(
#     #     period=5.0,
#     #     actions=[
#     #         ExecuteProcess(
#     #             cmd=['ros2', 'run', 'rover_sim', 'ign_rover_odom.py'],
#     #             name='go_goal_ign',
#     #             output='screen'
#     #         )
#     #     ]
#     # )



#     return LaunchDescription([
        
#         gazebo,
        
#         # ros_ign_bridge,
#         # sim_odom,
#         # madgwick_ndoe,
    
#         # sim_odom
#     ])

# ```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess

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
    # Get package share directory
    pkg_rover_sim = get_package_share_directory('rover_sim')
    gz_share = get_package_share_directory('ros_gz_sim')

    # World path
    world_file = os.path.join(pkg_rover_sim, 'worlds', 'test_world.sdf')

    # Launch Gazebo with the world file
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([gz_share, 'launch', 'gz_sim.launch.py'])),
        launch_arguments=[
            ("gz_args", [world_file, " -r -v "])  # -r (run), -v 4 (verbose)
        ]
    )

    bridge_config = PathJoinSubstitution([pkg_rover_sim, "config", "ros_gz_bridge.yaml"])
    
    ros_ign_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{"config_file": bridge_config}],
        output="screen"
    )
    return LaunchDescription([
        gazebo,
        ros_ign_bridge
    ])
# ```
