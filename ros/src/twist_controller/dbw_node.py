#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped, Twist
import math

from twist_controller import Controller

'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''

class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node')

        vehicle_mass = rospy.get_param('~vehicle_mass', 1736.35)
        fuel_capacity = rospy.get_param('~fuel_capacity', 13.5)
        brake_deadband = rospy.get_param('~brake_deadband', .1)
        decel_limit = rospy.get_param('~decel_limit', -5)
        accel_limit = rospy.get_param('~accel_limit', 1.)
        wheel_radius = rospy.get_param('~wheel_radius', 0.2413)
        wheel_base = rospy.get_param('~wheel_base', 2.8498)
        steer_ratio = rospy.get_param('~steer_ratio', 14.8)
        max_lat_accel = rospy.get_param('~max_lat_accel', 3.)
        max_steer_angle = rospy.get_param('~max_steer_angle', 8.)
        kp = 1
        ki = 1
        kd = 1

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)

        # TODO: Create `TwistController` object
        self.controller = Controller(kp, ki, kd, -200, 200, wheel_base, steer_ratio, 10, max_lat_accel, max_steer_angle)

        self._dbw_enabled = True
        self._twist_stamped = TwistStamped()
        self._curr_vel = Twist()

        # TODO: Subscribe to all the topics you need to
        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.dbw_enabled_cb)
        rospy.Subscriber('/twist_cmd',TwistStamped, self.twist_cmd_cb)
        rospy.Subscriber('/current_velocity',TwistStamped, self.cur_vel_cb)

        self.loop()

    def loop(self):
        rate = rospy.Rate(10) # 50Hz
        time = rospy.get_time()
        while time == 0:
            time = rospy.get_time()

        while not rospy.is_shutdown():
            rospy.loginfo("Looping in DBW")
            # TODO: Get predicted throttle, brake, and steering using `twist_controller`
            # You should only publish the control commands if dbw is enabled
            vel_mag = lambda a : math.sqrt((a.x ** 2) + (a.y **2) + (a.z ** 2))
            lin_vel = vel_mag(self._twist_stamped.twist.linear)
            ang_vel = vel_mag(self._twist_stamped.twist.angular)
            cur_vel_mag = vel_mag(self._curr_vel.linear)
            new_time= rospy.get_time()
            dt      = new_time - time
            time = new_time
            throttle, brake, steering = self.controller.control( lin_vel,
                                                                 ang_vel,
                                                                 cur_vel_mag,
                                                                 self._dbw_enabled,
                                                                 dt)
                                                                 #<proposed linear velocity>,
                                                                 #<proposed angular velocity>,
                                                                 #<current linear velocity>,
                                                                 #<dbw status>,
                                                                 #<any other argument you need>)
            if self._dbw_enabled == True:
               self.publish(throttle, brake, steering)
            rate.sleep()

    def cur_vel_cb(self, msg):
        self._curr_vel = msg.twist

    def twist_cmd_cb(self, msg):
        self._twist_stamped = msg

    def dbw_enabled_cb(self, msg):
        self._dbw_enabled = msg

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle * 100
        rospy.loginfo("Publishing throttle=%f ",throttle)
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)


if __name__ == '__main__':
    DBWNode()
