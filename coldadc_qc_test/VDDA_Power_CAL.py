import os
import os.path
import pwd
import sys
import numpy as np
import glob
import pandas as pd
import re
from matplotlib import pyplot as plt

start_num=int(input("Input Chip number where to start"))
end_num=int(input("Input Chip number where to end"))
loca_num=input("Input location number")
Test_bid=input("Input test board ID")
temp=input("Input temperature setting(rt or ln)")

file_list=[]
DIFF=[]
SE=[]
DIFF_ADD=[]
SE_ADD=[]
string_DIFF="External VDDA Power DIFF"
string_SE="External VDDA Power SE"

for chip_num in range (int(start_num),int(end_num)+1):
    
    file_list.append(glob.glob(os.path.dirname("/home/dune/ColdADC/test_results/coldadc_"+Test_bid+"_"+loca_num+"-"+str(chip_num)+"_"+temp+"_*"+"/*.txt")+"/test_report*.txt"))
    
print(file_list)
for lis in file_list:
    for folder in lis:
        print(folder)
        
        file_exists_Diff=os.path.exists(folder)

        if file_exists_Diff:

            file=open(folder)
            for line in file:
                if string_DIFF in line:
                    DIFF.append(re.findall("\d+\.\d+",line)[0])
                    DIFF_ADD.append(folder)
                if string_SE in line:
                    SE.append(re.findall("\d+\.\d+",line)[0])
                    SE_ADD.append(folder)
print(DIFF)
print(SE)
for i in range (len(DIFF)):
    DIFF[i]=float(DIFF[i])
    SE[i]=float(SE[i])
    if DIFF[i]>0.35 or SE[i]>0.35:
        print (i)
        print(DIFF[i])
        print(SE[i])
        print(DIFF_ADD[i])

fig1, axs1 = plt.subplots(1,1)
fig1.suptitle('VDDA power Comsuption '+str(start_num)+"~"+str(end_num)+" in "+temp)
fig1.set_size_inches(10,10)
se=np.array(SE)
diff=np.array(DIFF)
axs1.hist(DIFF,bins=2000,alpha=1,label="DIFF, mean:"+str(np.mean(diff))+",std:"+str(np.std(diff)))
axs1.hist(SE,bins=2000,alpha=0.85,label="SE, mean:"+str(np.mean(se))+",std:"+str(np.std(se)))
axs1.legend()
plt.xlim([0.3,0.4])
fig1.savefig("test_"+temp+".png")

            