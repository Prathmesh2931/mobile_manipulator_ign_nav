#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray, Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from rclpy.executors import MultiThreadedExecutor
import math


class OdomPublisher(Node):
    def __init__(self):
        super().__init__('vehicle_odom_publisher')

        self.subscription = self.create_subscription(
            PoseArray,
            '/dynamic_pose',
            self.pose_callback,
            10
        )

        self.odom_pub = self.create_publisher(Odometry, '/sim/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

    def pose_callback(self, msg: PoseArray):
        if not msg.poses:
            self.get_logger().warn("No poses received in /dynamic_pose")
            return

        pose = msg.poses[0]
        current_time = self.get_clock().now()

        yaw = 2.0 * math.atan2(pose.orientation.z, pose.orientation.w)
        yaw = (yaw + math.pi) % (2 * math.pi) - math.pi
        self.get_logger().info(f"yaw: {yaw:.3f}")

        odom_msg = Odometry()
        odom_msg.header.stamp = current_time.to_msg()
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_link'  # make sure matches TF

        odom_msg.pose.pose.position = pose.position
        odom_msg.pose.pose.orientation = pose.orientation
        odom_msg.twist.twist.linear.x = 0.0
        odom_msg.twist.twist.angular.z = 0.0

        self.odom_pub.publish(odom_msg)

        # Broadcast TF from odom → base_link
        tf_msg = TransformStamped()
        tf_msg.header.stamp = current_time.to_msg()
        tf_msg.header.frame_id = 'odom'
        tf_msg.child_frame_id = 'base_link'
        tf_msg.transform.translation.x = pose.position.x
        tf_msg.transform.translation.y = pose.position.y
        tf_msg.transform.translation.z = 0.0  # keep flat
        q = self.yaw_to_quaternion(yaw)
        tf_msg.transform.rotation.x = q[0]
        tf_msg.transform.rotation.y = q[1]
        tf_msg.transform.rotation.z = q[2]
        tf_msg.transform.rotation.w = q[3]

        self.tf_broadcaster.sendTransform(tf_msg)

    def yaw_to_quaternion(self, yaw):
        """Convert yaw angle (in radians) to quaternion (x, y, z, w)"""
        qz = math.sin(yaw / 2.0)
        qw = math.cos(yaw / 2.0)
        return (0.0, 0.0, qz, qw)


def main(args=None):
    rclpy.init(args=args)
    node = OdomPublisher()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
