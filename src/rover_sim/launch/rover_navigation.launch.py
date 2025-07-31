import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, GroupAction,
                            IncludeLaunchDescription, LogInfo, TimerAction,
                            SetEnvironmentVariable)  # Added this import
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    # Get the launch directory
    pkg_share = get_package_share_directory('rover_sim')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # Create the launch configuration variables
    namespace = LaunchConfiguration('namespace')
    use_namespace = LaunchConfiguration('use_namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')
    use_composition = LaunchConfiguration('use_composition')
    container_name = LaunchConfiguration('container_name')
    use_respawn = LaunchConfiguration('use_respawn')
    log_level = LaunchConfiguration('log_level')
    
    # Map fully qualified names to relative ones so the node's namespace can be prepended.
    # In case of the transforms (tf), currently, there doesn't seem to be a better alternative
    # https://github.com/ros/geometry2/issues/32
    # https://github.com/ros/robot_state_publisher/pull/30
    # TODO(orduno) Substitute with `PushNodeRemapping`
    #              https://github.com/ros2/launch_ros/issues/56
    remappings = [('/tf', 'tf'),
                  ('/tf_static', 'tf_static')]
    
    # Specify the actions
    map_yaml_file = LaunchConfiguration('map')
    
    # Create our own temporary YAML files that include substitutions
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'yaml_filename': map_yaml_file,
        'autostart': autostart,
        'namespace': namespace,
    }
    
    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites=param_substitutions,
        convert_types=True)
    
    stdout_linebuf_envvar = SetEnvironmentVariable(
        'RCUTILS_LOGGING_BUFFERED_STREAM', '1')
    
    # Declare the launch arguments
    declare_namespace_cmd = DeclareLaunchArgument(
        'namespace',
        default_value='',
        description='Top-level namespace')
    
    declare_use_namespace_cmd = DeclareLaunchArgument(
        'use_namespace',
        default_value='false',
        description='Whether to apply a namespace to the navigation stack')
    
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')
    
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_share, 'config', 'rover_nav2_params.yaml'),
        description='Full path to the ROS2 parameters file to use')
    
    declare_autostart_cmd = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the nav2 stack')
    
    declare_use_composition_cmd = DeclareLaunchArgument(
        'use_composition',
        default_value='False',
        description='Whether to use composed bringup')
    
    declare_container_name_cmd = DeclareLaunchArgument(
        'container_name',
        default_value='nav2_container',
        description='the name of conatiner that nodes will load in if use composition')
    
    declare_use_respawn_cmd = DeclareLaunchArgument(
        'use_respawn',
        default_value='False',
        description='Whether to respawn if a node crashes')
    
    declare_log_level_cmd = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='log level')
    
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(get_package_share_directory('turtlebot3'),
                                 'maps',
                                 'turtlebot3_world.yaml'),
        description='Full path to map yaml file to load')
    
    rviz_config_file = os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')
    
    # Launch RViz2 with the navigation configuration
    rviz_cmd = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen')
    
    # Make sure TF is properly published
    tf_remapper = Node(
        package='tf2_ros',
        executable='tf2_echo',
        arguments=['map', 'odom'],
        name='tf_remapper',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen')
    
    # Verify if map to odom transform is being published
    map_to_odom_check = ExecuteProcess(
        cmd=['bash', '-c', 'sleep 5 && ros2 run tf2_ros tf2_echo map odom'],
        output='screen')
    
    # Check if base_link to base_footprint transform is being published
    base_link_check = ExecuteProcess(
        cmd=['bash', '-c', 'sleep 5 && ros2 run tf2_ros tf2_echo base_link base_footprint'],
        output='screen')
    
    # Make sure the static transform from map to odom is published
    map_to_odom_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_static_tf',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
        arguments=['--frame-id', 'map', 
                  '--child-frame-id', 'odom',
                  '--x', '0', '--y', '0', '--z', '0',
                  '--roll', '0', '--pitch', '0', '--yaw', '0'])
    
    # Create the launch description and populate
    ld = LaunchDescription()
    
    # Set environment variables
    ld.add_action(stdout_linebuf_envvar)
    
    # Declare the launch options
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_use_namespace_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_autostart_cmd)
    ld.add_action(declare_use_composition_cmd)
    ld.add_action(declare_container_name_cmd)
    ld.add_action(declare_use_respawn_cmd)
    ld.add_action(declare_log_level_cmd)
    ld.add_action(declare_map_yaml_cmd)
    
    # Add the commands to the launch description
    ld.add_action(map_to_odom_static_tf)
    
    # Add the actions to launch all of the navigation nodes
    ld.add_action(IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir,
                                                  'launch',
                                                  'bringup_launch.py')),
        launch_arguments={'namespace': namespace,
                          'use_namespace': use_namespace,
                          'use_sim_time': use_sim_time,
                          'map': map_yaml_file,
                          'params_file': configured_params,
                          'autostart': autostart,
                          'use_composition': use_composition,
                          'use_respawn': use_respawn,
                          'container_name': container_name}.items()))

    # Add RViz
    ld.add_action(TimerAction(
        period=5.0,
        actions=[rviz_cmd]))
    
    # Add diagnostic commands
    ld.add_action(TimerAction(
        period=10.0,
        actions=[tf_remapper]))

    # Add TF tree visualization
    # ld.add_action(ExecuteProcess(
    #     cmd=['bash', '-c', 'sleep 15 && ros2 run tf2_tools view_frames'],
    #     output='screen'))
    
    # # Add topic list
    # ld.add_action(ExecuteProcess(
    #     cmd=['bash', '-c', 'sleep 20 && echo "TOPICS:" && ros2 topic list'],
    #     output='screen'))

    return ld