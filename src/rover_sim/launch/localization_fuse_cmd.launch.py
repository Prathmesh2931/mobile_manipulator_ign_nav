import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Package directories
    pkg_nav_stack = get_package_share_directory('nav_stack')
    
    # Launch arguments
    params_file = LaunchConfiguration('params_file')
    
    # Declare arguments
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_nav_stack, 'params', 'ekf1.yaml'),
        description='Path to the EKF parameters file'
    )
    
    # Robot localization (EKF)
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[params_file]
    )
    
    return LaunchDescription([
        declare_params_file_cmd,
        ekf_node
    ])