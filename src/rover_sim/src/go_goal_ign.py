#!/usr/bin/env python3

# import rclpy
# from rclpy.node import Node
# from geometry_msgs.msg import Twist, PoseStamped
# from nav_msgs.msg import Odometry
# import math
# import time


# class PurePursuitController(Node):
#     def __init__(self):
#         super().__init__('pure_pursuit_controller')

#         self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
#         self.odom_sub = self.create_subscription(Odometry, '/sim/odom', self.odom_callback, 10)
#         self.goal_sub = self.create_subscription(PoseStamped, '/goal_pose', self.goal_callback, 10)

#         self.timer = self.create_timer(0.1, self.control_loop)

#         self.current_pos = None
#         self.current_yaw = None
#         self.goal_pos = None
#         self.goal_yaw = None
#         self.last_odom_time = None

#         # Parameters
#         self.linear_k = 0.5
#         self.angular_k = 1.0
#         self.max_linear_speed = 0.3
#         self.max_angular_speed = 1.0

#         self.goal_reached_thresh = 0.05
#         self.yaw_tolerance = 0.1
#         self.odom_timeout = 1.0

#         self.goal_reached = False
#         self.get_logger().info("Pure Pursuit Go-To-Goal initialized.")

#     def odom_callback(self, msg):
#         self.current_pos = msg.pose.pose.position
#         self.current_yaw = self.quaternion_to_yaw(msg.pose.pose.orientation)
#         self.last_odom_time = time.time()

#     def goal_callback(self, msg):
#         self.goal_pos = msg.pose.position
#         self.goal_yaw = self.quaternion_to_yaw(msg.pose.orientation)
#         self.goal_reached = False
#         self.get_logger().info(f"Goal received: ({self.goal_pos.x:.2f}, {self.goal_pos.y:.2f})")

#     def quaternion_to_yaw(self, q):
#         """Convert quaternion to yaw (Euler Z)"""
#         siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
#         cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
#         return math.atan2(siny_cosp, cosy_cosp)

#     def normalize_angle(self, angle):
#         """Normalize to [-pi, pi]"""
#         return math.atan2(math.sin(angle), math.cos(angle))

#     def is_odom_fresh(self):
#         return self.last_odom_time is not None and (time.time() - self.last_odom_time) < self.odom_timeout

#     def control_loop(self):
#         if not self.is_odom_fresh() or self.current_pos is None or self.goal_pos is None:
#             self.publish_stop()
#             return

#         if self.goal_reached:
#             return

#         dx = self.goal_pos.x - self.current_pos.x
#         dy = self.goal_pos.y - self.current_pos.y
#         distance = math.hypot(dx, dy)

#         angle_to_goal = math.atan2(dy, dx)
#         heading_error = self.normalize_angle(angle_to_goal - self.current_yaw)

#         cmd = Twist()

#         if distance > self.goal_reached_thresh:
#             # Pure pursuit style control
#             cmd.linear.x = min(self.linear_k * distance, self.max_linear_speed)
#             cmd.angular.z = max(min(self.angular_k * heading_error, self.max_angular_speed), -self.max_angular_speed)

#             if abs(heading_error) > math.pi / 2:
#                 # Reverse if goal is behind
#                 cmd.linear.x *= -1
#                 cmd.angular.z *= -1

#             self.get_logger().info(f"Moving: dist={distance:.2f}, heading_err={math.degrees(heading_error):.1f}°")
#         else:
#             # Stop and align to final goal orientation
#             yaw_error = self.normalize_angle(self.goal_yaw - self.current_yaw)
#             if abs(yaw_error) > self.yaw_tolerance:
#                 cmd.angular.z = max(min(self.angular_k * yaw_error, self.max_angular_speed), -self.max_angular_speed)
#                 cmd.linear.x = 0.0
#                 self.get_logger().info(f"Aligning: yaw_err={math.degrees(yaw_error):.1f}°")
#             else:
#                 cmd.linear.x = 0.0
#                 cmd.angular.z = 0.0
#                 self.goal_reached = True
#                 self.get_logger().info("🎯 Goal fully reached with correct orientation.")

#         self.cmd_pub.publish(cmd)

#     def publish_stop(self):
#         self.cmd_pub.publish(Twist())

#     def destroy_node(self):
#         self.get_logger().info("Shutting down Pure Pursuit node.")
#         self.publish_stop()
#         super().destroy_node()


# def main(args=None):
#     rclpy.init(args=args)
#     try:
#         node = PurePursuitController()
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         print("Shutdown requested by user.")
#     finally:
#         node.destroy_node()
#         rclpy.shutdown()

# if __name__ == '__main__':
#     main()


#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
import math
import time

class PurePursuitStable(Node):
    def __init__(self):
        super().__init__('pure_pursuit_smooth_controller')

        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/sim/odom', self.odom_callback, 10)
        self.goal_sub = self.create_subscription(PoseStamped, '/goal_pose', self.goal_callback, 10)

        self.timer = self.create_timer(0.1, self.control_loop)

        self.current_pos = None
        self.current_yaw = None
        self.goal_pos = None
        self.goal_yaw = None
        self.last_odom_time = None

        # Parameters
        self.kp_linear = 0.5
        self.kp_angular = 1.0
        self.max_linear_speed = 0.25
        self.max_angular_speed = 1.0

        self.min_linear_speed = 0.05
        self.max_heading_error_to_move = 0.35  # radians (~20 degrees)

        self.distance_threshold = 0.07
        self.yaw_threshold = 0.08
        self.odom_timeout = 1.0

        self.goal_reached = False
        self.aligning_final_orientation = False


    def odom_callback(self, msg):
        self.current_pos = msg.pose.pose.position
        self.current_yaw = self.quaternion_to_yaw(msg.pose.pose.orientation)
        self.last_odom_time = time.time()

    def goal_callback(self, msg):
        self.goal_pos = msg.pose.position
        self.goal_yaw = self.quaternion_to_yaw(msg.pose.orientation)
        self.goal_reached = False
        self.get_logger().info(f"📍 New goal: x={self.goal_pos.x:.2f}, y={self.goal_pos.y:.2f}, yaw={math.degrees(self.goal_yaw):.1f}°")

    def quaternion_to_yaw(self, q):
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def normalize_angle(self, angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def is_odom_fresh(self):
        return self.last_odom_time and (time.time() - self.last_odom_time) < self.odom_timeout

    def control_loop(self):
        if not self.is_odom_fresh() or self.current_pos is None or self.goal_pos is None:
            self.publish_stop()
            return

        dx = self.goal_pos.x - self.current_pos.x
        dy = self.goal_pos.y - self.current_pos.y
        distance = math.hypot(dx, dy)
        angle_to_goal = math.atan2(dy, dx)

        heading_error = self.normalize_angle(angle_to_goal - self.current_yaw)
        final_yaw_error = self.normalize_angle(self.goal_yaw - self.current_yaw)

        cmd = Twist()

        if self.goal_reached:
            return

        # === New logic to lock final orientation state ===
        if distance <= self.distance_threshold or getattr(self, 'aligning_final_orientation', False):
            self.aligning_final_orientation = True

            # Final orientation phase
            if abs(final_yaw_error) > self.yaw_threshold:
                cmd.angular.z = max(min(self.kp_angular * final_yaw_error, self.max_angular_speed), -self.max_angular_speed)
                self.get_logger().info(f"🧭 Final orientation: yaw_err={math.degrees(final_yaw_error):.1f}°")
            else:
                # Reached final orientation
                cmd.angular.z = 0.0
                self.goal_reached = True
                self.aligning_final_orientation = False
                self.get_logger().info("✅ Goal and orientation fully reached!")

            cmd.linear.x = 0.0
        else:
            # Pursue target with heading correction
            if abs(heading_error) > self.max_heading_error_to_move:
                cmd.linear.x = 0.0
                cmd.angular.z = max(min(self.kp_angular * heading_error, self.max_angular_speed), -self.max_angular_speed)
                self.get_logger().info(f"↪ Aligning to path: yaw_err={math.degrees(heading_error):.1f}°")
            else:
                cmd.linear.x = max(self.min_linear_speed, min(self.kp_linear * distance, self.max_linear_speed))
                cmd.angular.z = max(min(self.kp_angular * heading_error, self.max_angular_speed), -self.max_angular_speed)
                self.get_logger().info(f"🚗 Driving: dist={distance:.2f}, heading_err={math.degrees(heading_error):.1f}°")

        self.cmd_pub.publish(cmd)


    def publish_stop(self):
        self.cmd_pub.publish(Twist())

    def destroy_node(self):
        self.get_logger().info("Shutting down.")
        self.publish_stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    try:
        node = PurePursuitStable()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("User interrupt")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
