import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import butter, lfilter, freqz,filtfilt,lfilter_zi
def butter_lowpass(cutoff, fs, order=5):
    return butter(order, cutoff, fs=fs, btype='low', analog=False)

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    zi = lfilter_zi(b, a)

    y = lfilter(b, a, data, zi=data[0]*zi)[0]
    return y

        # win   fail           ep   t_h   t_m   t_s
fig,allax=plt.subplots(1,3,figsize=(10,3),sharey=True)
plt.subplots_adjust(wspace=0)

path="/home/pablo/catkin_ws/src/ddrl_ge/src/save_model/environment__value.txt"
# path="stage_4_value_2.txt"
doc=pd.read_csv(path, delim_whitespace=True)
epi=doc["episode"].values
mask0=epi[1:]!=epi[:-1]
mask0=np.append(mask0,False)
doc.loc[mask0,"fail"]=1
win=doc["win"].values
fail=doc["fail"].values
###########TIME X GOAL
goal_x,goal_y=  -5.000e-01, 5.000e-01

mask=(doc["win"]==1)|(doc["fail"]==1)
ind=np.where(mask)[0]
ind = np.append(0,ind)
list_dis=[]

for i,j in enumerate(ind[:-1]):
    dist=np.sum(((doc.loc[ind[i]+1:ind[i+1],"robot_x"].values[1:]-doc.loc[ind[i]+1:ind[i+1],"robot_x"].values[:-1])**2+\
    (doc.loc[ind[i]+1:ind[i+1],"robot_y"].values[1:]-doc.loc[ind[i]+1:ind[i+1],"robot_y"].values[:-1])**2)**0.5)
    list_dis.append(dist)
mask1=(doc["win"].values==1)|(doc["fail"].values==1)


mask=((doc["goal_x"].values==goal_x ) & (doc["goal_y"].values==goal_y ))&(doc["win"].values==1)
mask_in=np.where(mask)[0]
indall=np.where(mask1)[0]

dist_indexes = np.where(mask[mask1])[0]

print(mask_in)
time=(doc[["t_h","t_m","t_s"]].iloc[mask_in])
time_b = np.zeros([len(time),3])
for i,m in enumerate(mask_in):
    ind_before = indall[np.where(m==indall)[0][0]-1]
    # print(ind_before)
    # tmp =doc[["t_h","t_m","t_s"]].iloc[ind_before+1]

    time_b[i]=(doc[["t_h","t_m","t_s"]].iloc[ind_before+1]).values

time_g=time.values-time_b
time_s=time_g[:,0]*3600+time_g[:,1]*60+time_g[:,2]

co_1path="#330019"
#

n_i=0
n_t=-1
list_dis=np.array(list_dis)

allax[0].plot(np.arange(len(time_s)),time_s,alpha=0.2,color='tab:orange')
allax[0].plot(np.arange(len(time_s))[n_i],time_s[n_i],zorder=200,color=co_1path,marker='*', markerfacecolor='magenta', markersize=12)
allax[0].plot(np.arange(len(time_s))[n_t],time_s[n_t],zorder=200,color=co_1path,marker='*', markerfacecolor='yellow', markersize=12)
# allax[0].text(np.arange(len(time_s))[n_t]-0.3,time_s[n_t]+1.8, str(int(time_s[n_t])), fontsize=10)
# allax[0].text(np.arange(len(time_s))[n_i]-0.3,time_s[n_t]+2.5, str(int(time_s[n_i])), fontsize=10)
allax[0].text(np.arange(len(time_s))[n_t]+3 ,time_s[n_t] , " time: "+str(int(time_s[n_t]))+"s"+"\n dist.: "+str(round(list_dis[dist_indexes][n_t],2))+"0"+"m", fontsize=10,va="center")
allax[0].text(np.arange(len(time_s))[n_i] ,time_s[n_i]+13.5, " time: "+str(int(time_s[n_i]))+"s"+"\n dist.: "+str(round(list_dis[dist_indexes][n_i],2))+"m", fontsize=10,va="top")
# allax[0].text(np.arange(len(time_s))[n_t]+3 ,time_s[n_t] , " time: "+str(int(time_s[n_t]))+"s"+"\n dist.: "+str(round(list_dis[dist_indexes][n_t],2))+"m", fontsize=10,va="center")
# allax[0].text(np.arange(len(time_s))[n_i] ,time_s[n_i]+13.5, " time: "+str(int(time_s[n_i]))+"s"+"\n dist.: "+str(round(list_dis[dist_indexes][n_i],2))+"m", fontsize=10,va="top")

# Filter requirements.
order = 2
fs = 40.0       # sample rate, Hz
cutoff = 3.1  # desired cutoff frequency of the filter, Hz
# Demonstrate the use of the filter.
# First make some data to be filtered.
T = len(time_s)/fs        # seconds
n = len(time_s) # total number of samples
# Filter the data, and plot both the original and filtered signals.
y = butter_lowpass_filter(time_s, cutoff, fs, order)
allax[0].plot(np.arange(len(time_s)),y,color='tab:orange',ls='-',label="Filtered Time")

[a.set_xlim(-11,390,50) for a in allax]
allax[0].set_ylim(0,50)
allax[0].set_xlim(-11,310,50)
#allax[0].set_xlim(-11,50,5)

allax[0].set_ylabel("Time(s)")
# allax[0].set_xlabel("Target"+" position"+str((float(goal_x),float(goal_y))))

# allax[1].set_xlabel("Target"+" position"+str((float(goal_x1),float(goal_y1))))
# allax[2].set_xlabel("Target"+" position"+str((float(goal_x1),float(goal_y1))))
# allax[2].legend(bbox_to_anchor=(1,1.16),loc="upper right")
allax[0].text(0.05,0.9,"DQN-Greedy",ha="left",transform=allax[0].transAxes,color="grey")
fig.text(0.13,1.03 ,"Environment 2",fontsize=15,transform=allax[0].transAxes,color="tab:blue")
# plt.grid()
# plt.savefig("fig/time_goal_en2_all.pdf",bbox_inches="tight")

plt.show()
