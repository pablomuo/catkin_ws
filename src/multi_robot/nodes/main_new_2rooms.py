from mpi4py import MPI
import numpy as np
import rospy
import random
from std_msgs.msg import Float32MultiArray
import tensorflow as tf
from agents import Agent
from environment import Behaviour
from collaboration import Collaboration
from reinforcenment import ReinforcementNetwork
from pathfinding import pathfinding
from configuration import Configuration
import os
import sys
import time
import os
import keras
import tensorflow as tf
gpu_options = tf.GPUOptions(allow_growth=True)
sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))
keras.backend.tensorflow_backend.set_session(sess)
from numba import cuda
tf.logging.set_verbosity(tf.logging.ERROR)

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()
name = MPI.Get_processor_name()
number_agents      = 1
state_size         = 28
action_size        = 6
episodes           = 19000
episode_step       = 60000
e                  = 0
global_step        = 0
number_episode     = 0
positions          = []
headings           = []
number_rooms       = 1
number_robot       = int(size)-(number_rooms*2) #         Number of robots with TWO CLOUDS

if size<=number_rooms:
    raise Exception("You need more cores than rooms!")

data1=None
data2=None

if rank==0:

    cam = '_1cam180'

    #Delete old folders of goal_box
    os.system('rm -r /home/pablo/catkin_ws/src/multi_robot/worlds/goal_box_'+"*")
    os.system('rm -r /home/pablo/catkin_ws/src/multi_robot/save_model/en'+"*")
    #Creates a file with the specified number of robots and targets
    # os.system('python many_robots.py'+" "+str([number_robot,number_rooms]))
    os.system('python many_robots_new.py'+" "+str(number_robot)+" "+str(number_rooms)+" "+cam)
    os.system("roslaunch multi_robot turtlebot3_multi.launch &")

comm.Barrier()

# Process to be followed for each agent
if rank>((number_rooms*2)-1):

    if (number_robot == number_rooms) and (number_rooms == 1):
        robot_rank = rank-1                                             #para una habitaciony un robot     (una CLOUD 1, una CLOUD 2, 1 robot)
    if (number_robot == number_rooms) and (number_rooms == 2):
        robot_rank = rank-number_rooms-1                                #para dos habitaciones y dos robots     (dos CLOUD 1, dos CLOUD 2, 2 robots)
    elif number_robot > number_rooms:
        robot_rank = rank-1                                             #para una habitacion y dos robots     (una CLOUD 1, una CLOUD 2, 2 robots)
    
    print('robot_rank', robot_rank)

    node = 'network'+str(robot_rank)
    rospy.init_node(node)
    # Instances

    agents  = Agent("agent"+str(robot_rank),action_size,state_size,number_episode,robot_rank)
    agents.call_sub("agent"+str(robot_rank),action_size,state_size,number_episode,robot_rank)
    print('agente with robot_rank started', robot_rank)

    agents.check_room()
    room_ID_c1 = agents.ID
    room_ID_c2 = room_ID_c1+number_rooms

    # The agent sends its ID to the CLOUD 1 in order to register.
    comm.send(rank, dest=room_ID_c1, tag=41+room_ID_c1*1000)
    sys.stdout.flush()
    # The agent sends its ID to the CLOUD 2 in order to register.
    comm.send(rank, dest=room_ID_c2, tag=51+room_ID_c2*1000)            #MODIFICAR DESTINOOOOOOO
    sys.stdout.flush()

    #comm.send(robot_rank, dest=1, tag=123)   #enviamos el robot_rank del robot a la CLOUD 2 para que puedar crear la clase agente del mismo robot
    #print("enviado a nube 2", robot_rank)

    #Initialization of variables to check if any agent is sending memory data
    init=True
    init_G=True
    print("robot, rank:", rank)


    # Resetting the position of each agent within the environment
    agents.environment.reset_gazebo()

    while not rospy.is_shutdown():
        """ Your main process which runs in thread for each chunk"""

        for e in range(agents.learning.load_epidose +1,episodes):
            e += 1
            # Reseting of variables
            agents.reset()
            time.sleep(0.5)
            # Resetting the position of the target and obtaining the distance to it
            agents.environment.reset(agents.robot_position_x, agents.robot_position_y)
            
            sys.stdout.flush()
            # Gets the initial state  (scan_data + [heading, current_distance,
            # wall_dist,goal_heading_initial])
            print("1. Reset position robots", robot_rank)
            s_initial = agents.get_initial_status
            print("get initial status", robot_rank)
            comm.send(s_initial, dest=room_ID_c2, tag=125+room_ID_c2*1000)   #enviamos el estado del robot a la CLOUD 2 
            print("enviado initial estado a la nube 2", robot_rank)


            for step in range(episode_step):
                agents.step = step
                # If the agent has a Pa (level of knowledge) > normal proces
                # (ability to execute backward action). Each collision ends
                # the episode and the agent is restarted in a random position
                # within the room where it crashed
                if agents.learning.Pa >agents.learning.normal_process:
                    if agents.process =="collision":
                        break
                    else:
                        pass
                
                #------------------------------------------------------
                # get accion of neuronal network or call evolve rule (path planning Algorithm) from CLOUD 2
                # agents.get_action_value()
                #if comm.Iprobe(source=1,tag=23+1000):
                action = comm.recv(source=room_ID_c2, tag=100+room_ID_c2*1000)
                sys.stdout.flush()
                #print("recivo act ")
                evolve_rule = comm.recv(source=room_ID_c2, tag=200+room_ID_c2*1000)
                #print("recibo evolve")
                q_value = comm.recv(source=room_ID_c2, tag=300+room_ID_c2*1000)
                sys.stdout.flush()

                #------------------------------------------------------
                
                
                print(" 2. Get accion of evolve rule ", evolve_rule, robot_rank)
                sys.stdout.flush()
                # According to the type of knowledge or processes. The agent will execute:
                if evolve_rule or agents.process =="collision":
                    agents.perform_action(agents.evolve()) # Get the action and Execute the action
                    agents.next_values() # Return next state, reward, done
                else:
                    agents.perform_action(action)# Execute the action
                    agents.next_values() # Return next state, reward, done
                print(" 3. Excecute action", robot_rank)
                sys.stdout.flush()

                # Save all data for plot
                agents.save_data_cloud(robot_rank,step,e,evolve_rule,q_value)
                print(" 4. save data", robot_rank)
                sys.stdout.flush()

                # Agent append data into memory D and Eps
                # data = state_initial,  action, reward, next_state, done
                agents.append_memory()
                print(" 5. Append memory", robot_rank)
                sys.stdout.flush()

                state_update = agents.state_initial
                comm.send(state_update, dest=room_ID_c2, tag=125+room_ID_c2*1000)   #enviamos el estado del robot a la CLOUD 2 
                print("position", agents.robot_position_x, agents.robot_position_y)
                #print("enviado estado actualizado a la nube 2")

                # The agent starts to send its memory to the corresponding cloud(ID)
                # to the room it is browsing
                # At the begining all robots have ID=0, which mean they are inside room 0
                if len(agents.learning.memory_D)>=10:
                    if init:
                        init=False
                        data=np.array(agents.learning.memory_D)
                        req=comm.issend(data, dest=room_ID_c1, tag=11+room_ID_c1*1000)
                        agents.learning.memory_D.clear()
                    else:
                        if MPI.Request.Test(req):
                            data=np.array(agents.learning.memory_D)
                            MPI.Request.Wait(req)
                            req=comm.issend(data, dest=room_ID_c1, tag=11+room_ID_c1*1000)
                            agents.learning.memory_D.clear()
                    print(" 6. ISend memory D", robot_rank)
                    sys.stdout.flush()

                if len(agents.learning.memory_GT)>=2:
                    if init_G:
                        init_G=False
                        data_G=np.array(agents.learning.memory_GT)
                        req_g=comm.issend(data_G, dest=room_ID_c1, tag=21+room_ID_c1*1000)
                        agents.learning.memory_GT.clear()
                    else:
                        if MPI.Request.Test(req_g):
                            data_G=np.array(agents.learning.memory_GT)
                            MPI.Request.Wait(req_g)
                            req_g=comm.issend(data_G, dest=room_ID_c1, tag=21+room_ID_c1*1000)
                            agents.learning.memory_GT.clear()

                    print("8. ISend memory GT", robot_rank)
                    sys.stdout.flush()

                
                #---------------------------------------------------------------
                
                # # if the agent has data to receive
                # if comm.Iprobe(source=agents.ID,tag=14+robot_rank+agents.ID*1000):
                #     print("12.0 before recieve networ ")
                #     sys.stdout.flush()
                #     weight_q=comm.recv(source=agents.ID,tag=14+robot_rank+agents.ID*1000)
                #     print("12.1 recieve q networ")
                #     sys.stdout.flush()
                #     weight_target=comm.recv(source=agents.ID,tag=14+size+robot_rank+agents.ID*1000)
                #     print("12.2 recieve target networ ")
                #     sys.stdout.flush()
                #     # set the cloud weights to the agent
                #     agents.time_to_update(weight_q,weight_target)

                #---------------------------------------------------------------

                # Check if the agent changed rooms
                agents.check_room()
                room_ID_c1 = agents.ID
                room_ID_c2 = room_ID_c1+number_rooms

                if agents.old_ID != agents.ID:             #revisar esto, si cambia de habitacion ya no tendra los weights, porque se reciben en CLOUD 2  
                    # Register in a new room
                    print("13.0 before subscription network ")
                    sys.stdout.flush()

                    comm.send(rank, dest=room_ID_c1, tag=41+room_ID_c1*1000)
                    print("13.1 The agent tells the CLOUD 1 that it is a new user ")
                    sys.stdout.flush()

                    comm.send(rank, dest=room_ID_c2, tag=51+room_ID_c2*1000)           #CAMBIAR DESTINOOOO
                    print("13.2 The agent tells the CLOUD 2 that it is a new user ")
                    sys.stdout.flush()
                    
                    #-----esto se enviaba cuando se cambiaba de habitacion, pero no es necesario, cuando un robot cambia de habitacion solo necesita indicarle a la nueva que ha entrado para que la tenga en su registro
                    #-----entonces cuando este dentro, el robot le enviara su estado y ya la nube 2 le indicara la accion a realizar-------------
                    # weight_q_to=agents.learning.q_model.get_weights()
                    # comm.send(weight_q_to, dest=agents.ID, tag=224+agents.ID*1000)
                    # print("13.2 The agent sends its q network to the new cloud ")
                    # sys.stdout.flush()
                    # weight_target_to=agents.learning.target_model.get_weights()
                    # comm.send(weight_target_to, dest=agents.ID, tag=300+agents.ID*1000)
                    # print("13.3 The agent sends its target network to the new cloud")
                    # sys.stdout.flush()
                    #-------------------------------------------------------------------------------------------
                    
                    # Unsubscribe from old room IN cloud 1
                    comm.send(rank, dest=agents.old_ID, tag=81+agents.old_ID*1000)                                      #CAMBIO
                    print("13.3 after Unsubscribe agent" +str(robot_rank)+" in room "+ str(agents.old_ID) + " in CLOUD 1")      
                    sys.stdout.flush()

                    # Unsubscribe from old room IN cloud 2
                    comm.send(rank, dest=(agents.old_ID+number_rooms), tag=91+(agents.old_ID+number_rooms)*1000)             #CAMBIO DOBLE
                    print("13.3 after Unsubscribe agent" +str(robot_rank)+" in room"+ str(agents.old_ID) + " in CLOUD 2")      
                    sys.stdout.flush()

                # When the agent achieves the target, it calculates its total
                #reward and sends it to the different memories
                agents.work_out_best_state()
                print("15 after work out state", robot_rank)
                sys.stdout.flush()

                agents.learning.save_model(robot_rank,e)
                print("16 after learning save model", robot_rank)
                sys.stdout.flush()

                if agents.time_out(step):
                    break
                if agents.done:
                    #check if has to go at the begining of done
                    agents.keep_or_reset()
                    # agents.learning.update_target_network()
                    agents.done =False
                    if agents.finish:
                        agents.finish = False
                        break
                    if evolve_rule:
                        agents.process="collision"
                        e +=1
                        agents.cont+=1
                        agents.learning.increase_fact()
                        print("Eviamos a las nubes aviso para actualizar Pbest y Pa")
                        comm.send(e, dest=room_ID_c2, tag=321+room_ID_c2*1000)        # enviamos un alerta a la nube dos para que actualice Pbest y Pa
                        agents.last_heading=list()
                        agents.environment.reset(agents.robot_position_x, agents.robot_position_y)
                        if agents.cont > 20:
                            agents.cont=0
                            break
                        else:
                            pass
                    else:
                        break
                    print("17 after done", robot_rank)
                    sys.stdout.flush()
            #Increase Pa
            agents.learning.increase_fact()
            comm.send(e, dest=room_ID_c2, tag=321+room_ID_c2*1000)        # enviamos un alerta a la nube dos para que actualice Pbest y Pa
            print("18 after increse factor", robot_rank)
            sys.stdout.flush()

# Process to be followed for each cloud
# One cloud is one room
if rank<number_rooms:                    #revisar si el rank de la CLOUD 1 hay que modificarlo como en el rank_robot
    with tf.device('/cpu:0'):
        print("nube 1, rank:", rank)
        cluster=ReinforcementNetwork(state_size,action_size,number_episode,load=False)
        step=0
        Room_member_ID=[]
        while not rospy.is_shutdown():
            # Registering to the room
            while comm.Iprobe(source=MPI.ANY_SOURCE,tag=41+rank*1000):
                member_ID=comm.recv(source=MPI.ANY_SOURCE, tag=41+rank*1000)
                Room_member_ID.append(member_ID)
                print("14.0 ROBOT before merge ANOTHER AREA"+str(rank)+": ", Room_member_ID)
                sys.stdout.flush()

                #----cuando llega un nuevo robot a la habitacion, ya no es necesario que envie sus pesos, simplemente con eviar su estado en cada momento, la nube le dara la accion
                # if comm.Iprobe(source=MPI.ANY_SOURCE,tag=224+rank*1000):
                #     weight_q_to=comm.recv(source=MPI.ANY_SOURCE, tag=224+rank*1000)
                #     print("14.1 cloud recives q network to MERGE ")
                #     sys.stdout.flush()

                #     weight_target_to=comm.recv(source=MPI.ANY_SOURCE,tag=300+rank*1000)
                #     print("14.2 cloud recives target network to MERGE")
                #     sys.stdout.flush()

                #     cluster.merge_target_cloud(weight_q_to,weight_target_to)
                #     print("14.3  cloud MERGE ANOTHER AREA")
                #     sys.stdout.flush()

            # Unsubscribe from room
            while comm.Iprobe(source=MPI.ANY_SOURCE,tag=81+rank*1000):
                try :
                    member_ID=comm.recv(source=MPI.ANY_SOURCE, tag=81+rank*1000)
                    Room_member_ID.remove(member_ID)
                    print("14.4 list of members in CLOUD 1 Unsubscribe, agent"+str(rank)+" unsubscribed: ", Room_member_ID)
                    sys.stdout.flush()
                except:
                    print("14.5 Error in list of members Unsubscribe")
                    sys.stdout.flush()
            
            step+=1
            # Ask if any agent has sent data from memory_D
            if comm.Iprobe(source=MPI.ANY_SOURCE,tag=11+rank*1000):
                print("7.0 waiting append data memory D to ",rank)
                sys.stdout.flush()

                data = comm.recv(source=MPI.ANY_SOURCE, tag=11+rank*1000)
                print("7.1 recive append data",rank)
                sys.stdout.flush()

                for i in range(len(data)):
                    cluster.append_D(data[i][0], data[i][1],data[i][2], data[i][3], data[i][4])
                print("7.2 I Recive memory D")
                sys.stdout.flush()

            # Ask if any agent has sent data from memory_G
            if comm.Iprobe(source=MPI.ANY_SOURCE,tag=21+rank*1000):
                print("9.1 wainting second append data",rank)
                sys.stdout.flush()

                data_G = comm.recv(source=MPI.ANY_SOURCE, tag=21+rank*1000)
                print("9.2 reciving second append data",rank)
                sys.stdout.flush()

                for p in range(len(data_G)):
                    cluster.append_GT(data_G[p][0], data_G[p][1],data_G[p][2], data_G[p][3], data_G[p][4])
                print("9.3 Irecived  memory GT")
                sys.stdout.flush()

            if comm.Iprobe(source=rank+number_rooms,tag=333+rank*1000):
                print("Recibimos alerta desde CLOUD 1 para actualizar Pbes y Pa")
                sys.stdout.flush()
                alert=comm.recv(source=rank+number_rooms,tag=333+rank*1000)
                sys.stdout.flush()
                cluster.increase_fact()
                print("Pbest CLOUD 1: ", cluster.Pbest)
                print("Pa CLOUD 1: ", cluster.Pa)

            # Cluster starts training the network q
            train= cluster.start_training()
            print("10 Training")
            sys.stdout.flush()

            # Updating the networks of the registered agents in the cloud
            # with the current cloud network
            #print(step)
            #print(train)
            if (step%20==0) and (train==True):
                weight_q      = cluster.q_model.get_weights()
                weight_target = cluster.q_model.get_weights()
                for g in Room_member_ID:                                 #revisar junto con el real rankkkkkkkkkkkkkk
                    # if the agent g is not reciving data
                    if not comm.Iprobe(source=MPI.ANY_SOURCE,tag=14+rank+g*1000):            #revisaaaaar
                        print("11.0 wainting for send network ", g, Room_member_ID)
                        sys.stdout.flush()
                        comm.send(weight_q,dest=(rank+number_rooms),tag=14+g*1000)
                        print("11.1 finish to send q network to ", g)
                        sys.stdout.flush()
                        comm.send(weight_target,dest=(rank+number_rooms),tag=24+g*1000)
                        print("11.2 finish to send target network to ", g)
                        sys.stdout.flush()

            if (step%50==0) and (train==True):
                cluster.update_target_cloud()
                print( "19.1 UPDATE TARGET NETWORK CLOUD")
                sys.stdout.flush()

            if step%1000==0:
                cluster.save_model(rank,step)     #revisar si el rank de la CLOUD 1 hay que modificarlo como en el rank_robot
                print("20 Save model")
                sys.stdout.flush()

            if not train:
                time.sleep(2)
                print("21 Sleeping")
                sys.stdout.flush()
            rospy.sleep(1)



if rank>number_rooms-1 and rank<number_rooms*2:          #tiene que haber un registro de los robots que hay en la nube, igual que sucede en la nube 1
    # with tf.device('/cpu:1'):
    print("nube 2, rank:", rank)
    cluster2=ReinforcementNetwork(state_size,action_size,number_episode,load=False)
    
    # state_initial = comm.recv(source=2, tag=121) 
    # sys.stdout.flush()
    # print("initial_status RECEIVED")

    Room_member_ID_cloud2=[]    
    while not rospy.is_shutdown():

        while comm.Iprobe(source=MPI.ANY_SOURCE,tag=51+rank*1000):
            member_ID_cloud2=comm.recv(source=MPI.ANY_SOURCE, tag=51+rank*1000)
            Room_member_ID_cloud2.append(member_ID_cloud2)
            print("14.0 ROBOT before merge ANOTHER CLOUD 2 AREA"+str(rank-number_rooms)+": ", Room_member_ID_cloud2)
            sys.stdout.flush()

                #----cuando llega un nuevo robot a la habitacion, ya no es necesario que envie sus pesos, simplemente con eviar su estado en cada momento, la nube le dara la accion
                # if comm.Iprobe(source=MPI.ANY_SOURCE,tag=224+rank*1000):
                #     weight_q_to=comm.recv(source=MPI.ANY_SOURCE, tag=224+rank*1000)
                #     print("14.1 cloud recives q network to MERGE ")
                #     sys.stdout.flush()

                #     weight_target_to=comm.recv(source=MPI.ANY_SOURCE,tag=300+rank*1000)
                #     print("14.2 cloud recives target network to MERGE")
                #     sys.stdout.flush()

                #     cluster.merge_target_cloud(weight_q_to,weight_target_to)
                #     print("14.3  cloud MERGE ANOTHER AREA")
                #     sys.stdout.flush()

        # Unsubscribe from room
        while comm.Iprobe(source=MPI.ANY_SOURCE,tag=91+rank*1000):
            try :
                member_ID_rem=comm.recv(source=MPI.ANY_SOURCE, tag=91+rank*1000)
                Room_member_ID_cloud2.remove(member_ID_rem)
                print("14.4 list of members in CLOUD 2 Unsubscribe, agent"+str(rank)+" unsubscribed: ", Room_member_ID_cloud2)
                sys.stdout.flush()
            except:
                print("14.5 Error in list of members Unsubscribe")
            

        for n_robot in Room_member_ID_cloud2:
            # get accion of neuronal network or call evolve rule (path planning Algorithm)
            
            state_initial = comm.recv(source=n_robot, tag=125+rank*1000)    #CAMBIO
            sys.stdout.flush()

            act, evolve_r = cluster2.get_action(np.array(state_initial))
            q_val = cluster2.q_value

            comm.send(act,dest=n_robot,tag=100+rank*1000)         #CAMBIO
            sys.stdout.flush()
            #print("envio act y evolve")
            comm.send(evolve_r,dest=n_robot,tag=200+rank*1000)     #CAMBIO
            sys.stdout.flush()
            comm.send(q_val,dest=n_robot,tag=300+rank*1000)       #CAMBIO
            sys.stdout.flush()

            
            # # if the CLOUD 2 has weights to receive from CLOUD 1
            if comm.Iprobe(source=(rank-number_rooms),tag=14+n_robot*1000):
                print("12.0 before recieve networ ")
                sys.stdout.flush()
                weight_q=comm.recv(source=(rank-number_rooms),tag=14+n_robot*1000)
                print("12.1 recieve q networ")
                sys.stdout.flush()
                weight_target=comm.recv(source=(rank-number_rooms),tag=24+n_robot*1000)
                print("12.2 recieve target networ ")
                sys.stdout.flush()
                # set the cloud weights to the agent
                #agents.time_to_update(weight_q,weight_target)
                cluster2.update_target_network(weight_q,weight_target)
            
            if comm.Iprobe(source=n_robot,tag=321+rank*1000):
                print("Recibimos alerta desde agente para actualizar Pbes y Pa")
                sys.stdout.flush()
                alert=comm.recv(source=n_robot,tag=321+rank*1000)
                sys.stdout.flush()
                cluster2.increase_fact()
                print("Pbest CLOUD 2: ", cluster2.Pbest)
                print("Pa CLOUD 2: ", cluster2.Pa)
                print("Enviamos alerta a CLOUD 1para actualizar Pbes y Pa")
                comm.send(alert,dest=rank-number_rooms,tag=333+(rank-number_rooms)*1000)
                sys.stdout.flush()
            


