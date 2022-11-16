import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
fig, allax = plt.subplots(1,3,figsize=(10,3),sharey=True)
plt.subplots_adjust(wspace=0)
hea="  step    episode   a          reward        score      robot_x      robot_y      goal_x       goal_y   e_r    q_value       b_time    win   fail           Pa   t_h   t_m   t_s "
doc  = pd.read_csv("environment__value.txt", usecols =range(18), skiprows=1, header=0, engine="python", delim_whitespace=True,names=hea.split())

print(doc)
epi=doc["episode"].values
win=doc["win"].values
fail=doc["fail"].values
unique=np.unique(doc[["goal_x","goal_y"]].values,axis=0)
mask=win==1
win_d=doc[mask]
fail_d=doc[fail==1]
values_goal=win_d.groupby(["goal_x","goal_y"])["win"].count()
values_fail=fail_d.groupby(["goal_x","goal_y"])["fail"].count()

f=(values_fail+values_goal)-values_goal-values_fail
f[np.isnan(f)]=0
f=f+values_fail
f[np.isnan(f)]=0
values_fail=f

g=((values_goal+values_fail)-values_fail-values_goal)
g[np.isnan(g)]=0
g=g+values_goal
g[np.isnan(g)]=0
values_goal=g
valu_g=np.arange(values_fail.count())

s=values_fail+values_goal
sortkey = np.argsort(values_fail.values.astype(float)/s.values)
s=s.values[sortkey].astype(float)
values_fail=values_fail.values[sortkey]
values_goal=values_goal.values[sortkey]
unique=unique[sortkey,:]
allax[2].bar(valu_g,values_fail/s,width=0.5,label="# Fails",color="tab:orange")
allax[2].bar(valu_g,values_goal/s,width=0.5,bottom=values_fail/s,label="# Goals",color="tab:cyan")
labels=[str(unique[i,0])+","+str(unique[i,1]) for i in range(unique.shape[0])]
allax[2].set_xticks(valu_g )
allax[2].set_xticklabels( labels,rotation=90)

allax[1].set_xlabel("Target Positions")
allax[0].set_ylabel("Percentage [%]")
fig.text(0.13,1.03 ,"Environment",fontsize=12,transform=allax[0].transAxes,color="black")
allax[0].set_ylim(0,1.19)
allax[0].text( 0.05,0.9 ,"DQN-Greedy",ha="left",transform=allax[0].transAxes,color="grey")
allax[1].text( 0.05,0.9 ,"DDPG-PER",ha="left",transform=allax[1].transAxes,color="grey")
allax[2].text( 0.05,0.9 ,"DDRL-EG",ha="left",transform=allax[2].transAxes,color="grey")
plt.legend(loc="upper right",bbox_to_anchor=(1,1.15),ncol=2)
#plt.savefig("/home/pablo/Documents/Fig/histogram.pdf",bbox_inches="tight")
fig.savefig(f"histogram.pdf", dpi=250)
plt.show()
