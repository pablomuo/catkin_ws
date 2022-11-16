#! /usr/bin/env python
# coding=utf-8

import rospy
import message_filters
import numpy as np
from sensor_msgs.msg import LaserScan

rospy.init_node("camera_sync_1cam")

def callback(camera, back_camera):
    val_max = 0
    sum_data = 0
    promedio = 0
    scan_max = 1
    scan_data_pre = []
    scan_data = 24*[0]
    
    #print(scan.header)
    for i in range(len(camera.ranges)*2):
        if i < 12:
            if camera.ranges[i] == float("Inf"):
                scan_data_pre.append(3.5)
                val_max = 3.5
            elif np.isnan(camera.ranges[i]):
                scan_data_pre.append(0)
                val_max = 0
            else:
                scan_data_pre.append(camera.ranges[i])
                val_max = camera.ranges[i]
            
            sum_data = sum_data + val_max
            if camera.ranges[i] > scan_max:
                if camera.ranges[i] <= 2:
                    scan_max = camera.ranges[i]
                else:
                    pass
            else: 
                pass

        if i == 12:
            promedio = sum_data/12
            if scan_max == 1:           #son todos o mayores de 2 o menor de 1, pillamos el promedio entonces
                scan_max = promedio
                if scan_max > 2:
                    scan_max = 2
        
        if i >= 12:
            scan_data_pre.append(scan_max)
    
    scan_data[0:6] = scan_data_pre[6:12]
    scan_data[6:18] = scan_data_pre[12:24]
    scan_data[18:24] = scan_data_pre[0:6]

    pub.publish(header = camera.header, ranges = scan_data)

front_sub = message_filters.Subscriber("/camera", LaserScan)
back_sub = front_sub

pub = rospy.Publisher('/camera_sync_1cam', LaserScan, queue_size=1)

# ats = message_filters.ApproximateTimeSynchronizer([front_sub, back_sub], queue_size=5, slop=0.01)
ats = message_filters.TimeSynchronizer([front_sub, back_sub], queue_size=1)
ats.registerCallback(callback)

rospy.spin()


