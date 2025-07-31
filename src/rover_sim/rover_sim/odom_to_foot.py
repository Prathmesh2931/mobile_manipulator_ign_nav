#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import tf2_ros
from geometry_msgs.msg import TransformStamped

class OdomToTF(Node):
    def __init__(self):
        super().__init__('odom_to_base_footprint_tf')
        
        # Subscribe to the odometry topic - with a leading slash to ensure absolute path
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',  # Added leading slash to ensure we get the correct topic
            self.odom_callback,
            10)
            
        # Create a transform broadcaster
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        self.get_logger().info('OdomToTF node started - Listening for /odom messages')
        
        # Add diagnostics timer to check if we're receiving messages
        self.timer = self.create_timer(5.0, self.timer_callback)
        self.received_msg = False

    def timer_callback(self):
        """Check if we've received any messages since the last timer callback"""
        if not self.received_msg:
            self.get_logger().warn('No odometry messages received in the last 5 seconds!')
            # List topics to help diagnose
            self.get_logger().info('Available topics:')
            self.get_logger().info(str(self.get_subscribed_topics()))
        else:
            self.get_logger().info('Odometry messages are being received properly')
            
        self.received_msg = False

    def odom_callback(self, msg):
        # Indicate we've received a message
        self.received_msg = True
        
        # Create a transform from odom to base_footprint based on odometry message
        t = TransformStamped()
        
        # Fill in the header
        t.header.stamp = msg.header.stamp
        t.header.frame_id = 'odom'
        
        # Fill in the child frame ID
        t.child_frame_id = 'base_footprint'
        
        # Copy the translation
        t.transform.translation.x = msg.pose.pose.position.x
        t.transform.translation.y = msg.pose.pose.position.y
        t.transform.translation.z = 0.0  # Set Z to 0 for base_footprint
        
        # Copy the rotation
        t.transform.rotation = msg.pose.pose.orientation
        
        # Broadcast the transform
        self.tf_broadcaster.sendTransform(t)
        
        # Log occasionally
        if hasattr(self, 'log_counter'):
            self.log_counter += 1
            if self.log_counter > 100:  # Log every ~100 messages
                self.get_logger().info(f'Publishing transform: odom → base_footprint: {t.transform.translation.x:.2f}, {t.transform.translation.y:.2f}')
                self.log_counter = 0
        else:
            self.log_counter = 0

def main(args=None):
    rclpy.init(args=args)
    node = OdomToTF()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        node.get_logger().error(f'Error: {str(e)}')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()