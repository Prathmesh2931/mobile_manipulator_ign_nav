#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
import math

class GoToGoal(Node):
    def __init__(self):
        super().__init__('go_to_goal')
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.goal_sub = self.create_subscription(PoseStamped, '/goal_pose', self.goal_callback, 10)
        self.timer = self.create_timer(0.1, self.control_loop)

        self.current_position = None
        self.current_yaw = None
        self.desired_yaw = None
        self.goal_position = None

        # Control Parameters
        self.kp_angular = 0.5 
        self.kp_linear = 0.4  
        self.linear_speed = 0.55  
        self.distance_threshold = 0.15  
        self.orient_threshold = 0.25 
        self.max_angular_speed = 0.99  
        self.min_linear_speed = 0.55
        self.min_angular_speed = 0.99

        self.stage = 0  # 0: rotate to goal dir, 1: move to goal, 2: final yaw, 3: done

    def odom_callback(self, msg):
        self.current_position = msg.pose.pose.position
        orientation_q = msg.pose.pose.orientation
        self.current_yaw = 2.0 * math.atan2(orientation_q.z, orientation_q.w)
        # self.get_logger().info(f"Yaw is {self.current_yaw}")
    def goal_callback(self, msg):
        self.goal_position = msg.pose.position
        orientation_q = msg.pose.orientation
        self.desired_yaw = 2.0 * math.atan2(orientation_q.z, orientation_q.w)
        self.stage = 0  # Reset to start from the beginning
        self.get_logger().info(f"New Goal: ({self.goal_position.x:.2f}, {self.goal_position.y:.2f}), Desired Yaw: {self.desired_yaw:.2f}")

    def normalize_angle(self, angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def control_loop(self):
        if self.current_position is None or self.goal_position is None or self.desired_yaw is None:
            return

        dx = self.goal_position.x - self.current_position.x
        dy = self.goal_position.y - self.current_position.y
        distance = math.sqrt(dx**2 + dy**2)
        yaw_to_goal = math.atan2(dy, dx)
        yaw_error_to_goal = self.normalize_angle(yaw_to_goal - self.current_yaw)
        final_orient_error = self.normalize_angle(self.desired_yaw - self.current_yaw)

        cmd = Twist()

        # -------- Stage 0: Face the goal direction --------
        if self.stage == 0:
            if abs(yaw_error_to_goal) > self.orient_threshold:
                angular = self.kp_angular * yaw_error_to_goal
                cmd.angular.z = max(angular, self.min_angular_speed) if angular > 0 else min(angular, -self.min_angular_speed)
                cmd.angular.z = max(-self.max_angular_speed, min(cmd.angular.z, self.max_angular_speed))
                self.get_logger().info(f"[Stage 0] Turning to face goal: yaw_error = {yaw_error_to_goal:.2f}, angular.z = {cmd.angular.z:.2f}")
            else:
                self.stage = 1  # Move to next stage
                self.get_logger().info("[Stage 0] Done facing goal. Switching to stage 1.")

        # -------- Stage 1: Move toward the goal --------
        elif self.stage == 1:
            if distance > self.distance_threshold:
                linear = self.kp_linear * distance
                # cmd.linear.x = max(linear, self.min_linear_speed) if linear > 0 else min(linear, -self.min_linear_speed)
                cmd.linear.x=self.linear_speed
                self.get_logger().info(f"[Stage 1] Moving to goal: distance = {distance:.2f}, linear.x = {cmd.linear.x:.2f}")
            else:
                self.stage = 2  # Move to orientation correction
                self.get_logger().info("[Stage 1] Reached goal position. Switching to stage 2.")

        # -------- Stage 2: Adjust final orientation --------
        elif self.stage == 2:
            if abs(final_orient_error) > self.orient_threshold:
                angular = self.kp_angular * final_orient_error
                cmd.angular.z = max(angular, self.min_angular_speed) if angular > 0 else min(angular, -self.min_angular_speed)
                cmd.angular.z = max(-self.max_angular_speed, min(cmd.angular.z, self.max_angular_speed))
                self.get_logger().info(f"[Stage 2] Final orientation: error = {final_orient_error:.2f}, angular.z = {cmd.angular.z:.2f}")
            else:
                self.stage = 3
                self.get_logger().info("[Stage 2] Final orientation reached. Done.")

        # -------- Stage 3: Done --------
        elif self.stage == 3:
            self.get_logger().info("[Stage 3] Goal reached completely. Waiting...")

        self.cmd_vel_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = GoToGoal()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
