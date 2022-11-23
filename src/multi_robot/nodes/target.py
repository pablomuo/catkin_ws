#!/usr/bin/env python
#################################################################################
#Copyright 2022 Elizabeth
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#distributed under the License is distributed on an "AS IS" BASIS,
#See the License for the specific language governing permissions and
#limitations under the License.
#################################################################################


import rospy
import numpy as np
import time
import os
import random
from gazebo_msgs.srv import SpawnModel, DeleteModel
from gazebo_msgs.msg import ModelStates
from geometry_msgs.msg import Pose

class Target(object):
    def __init__(self,agent_name,ID):
        self.modelPath = os.path.dirname(os.path.realpath(__file__))
        self.modelPath = self.modelPath.replace('multi_robot/nodes',
                                                'multi_robot/worlds/goal_box_'+str(agent_name)+'/model_'+str(agent_name)+'.sdf')
        # self.f=str(agent_name)
        self.agent_name= open(self.modelPath, 'r')
        self.model = self.agent_name.read()
        self.target_position = Pose()
        # FOR BOX
        self.ID=ID
        self.ini=random.choice(range(4))
        self.init_goal_x = [4,-2.5,-2,4][self.ini]
        self.init_goal_y = [4,0.5,-3,-1][self.ini]
        # FOR CORRIDOR
        # self.init_goal_x = 0.5
        # self.init_goal_y = 0.5
        self.target_position.position.x = self.init_goal_x
        self.target_position.position.y = self.init_goal_y
        self.modelName = 'goal_'+str(agent_name)
        self.last_goal_x = self.init_goal_x
        self.last_goal_y = self.init_goal_y
        self.last_index = 0
        self.check_model = False
        self.index = 0


    def respawnModel(self):
        while True:
                rospy.wait_for_service('gazebo/spawn_sdf_model')
                spawn_model_prox = rospy.ServiceProxy('gazebo/spawn_sdf_model', SpawnModel)
                spawn_model_prox(self.modelName, self.model, 'robotos_name_space', self.target_position, "world")
                rospy.loginfo("Goal position : %.1f, %.1f ", self.target_position.position.x,
                              self.target_position.position.y )
                break
    def deleteModel(self):
        while True:
                rospy.wait_for_service('gazebo/delete_model')
                del_model_prox = rospy.ServiceProxy('gazebo/delete_model', DeleteModel)
                del_model_prox(self.modelName)
                break

    def getPosition(self, position_check=False, delete=False):
        if delete:
            self.deleteModel()
        while position_check:
            if self.ID==0:
                goal_x_list = [9.5, -9.2, -9.2, 4.8, 3.3, 4.3, 2.3, 9.6]
                goal_y_list = [8.7,  8.8,    5, 2.3, 4.3, 8.8, 1.9, 1.9]
                # goal_x_list = [-2,   1,      -3]
                # goal_y_list = [-3.2, 3.2,  10]
                # goal_x_list = [-2,   1,   2, -2, 3, -3, -1.5, 1, 2,   -2,   3,   4,   -4,-4,-4.5, 3,  -2.3, 2,   -3, -3.5, 1.5,  0 ,  4,-1.5, 3, 3,    0,  -4,    4,1.5    ,-3]
                # goal_y_list = [-3.2, 3.2, 2, -4, 4, -4, 2,   -3, -3.5, 3.3, -4, -0.5 , 4,-4, 0,   -0.5, 0,   -2, -1.5, 3.5,-3.5, -4,   4, 2.5, 2,-2.6,    5,   3, -3, 1.5  ,10]

            if self.ID==1:
                goal_x_list = [ 9.5,  9.6,  3, -2, -8.5, -9, -3.9, 0.77]
                goal_y_list = [-1.2, -9.6, -3, -3, -1.1, -9, -9.1, -5.1]
                # goal_x_list =[-1.5,-3,0, 2, 0,-2,2,4, 4, -3   ,2]
                # goal_y_list =[ 6.5,10,6,6.5,9,10,10,9,6.5,6   ,2]

            # if self.ID==2:
            #     goal_x_list =[-7,-10,-9,-9,-6,-6,-6,2]
            #     goal_y_list =[7  ,10, 7,10, 7, 9,10,2]


            # if self.ID==3:
            #     goal_x_list =[-10.5,10.5,-12,-7,-10,10,-6,-6, -10,-10 ,2]
            #     goal_y_list =[-3,   3,     0, 0,  4,-4,3.5,-3.5, 2,-2   ,2]

            # goal for corridor
            # goal_x_list = [0.5,1,    2  ,3 , 4  ,7 , 9  ,  12,   4.5, 7.5,-1,-4, -1,-5,  -7.5,-9,-10,-11,9.5]
            # goal_y_list = [0.5,1,   0.5, 1,-0.8, 0.8,  -1.5,0,  -1.5,-1.5,-1,-0.5,1,-1.2,1,   -1, 1,  0, 1.5]

            self.index = np.random.randint(0, len(goal_y_list), 1)[0]


            # self.index = random.randrange(0, len(goal_y_list))
            if self.last_index == self.index:
                position_check = True

            else:
                self.last_index = self.index
                position_check = False

            self.target_position.position.x = goal_x_list[self.index]
            self.target_position.position.y = goal_y_list[self.index]

        time.sleep(0.5)
        self.respawnModel()

        self.last_goal_x = self.target_position.position.x
        self.last_goal_y = self.target_position.position.y

        return self.target_position.position.x, self.target_position.position.y

    @property
    def position(self):
        return (self.target_position.position.x ,self.target_position.position.y)
