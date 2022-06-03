""" Calculates INL and DNL from sine wave data. Adjust minbin and maxbin
    depending on your data.
    Ported from MATLAB to Python by C. Grace (crgrace@lbl.gov)
    Original MATLAB (dnl_inl_sin.m) by Boris Murmann (Aug 2002)
"""

import numpy as np
import matplotlib.pyplot as plt
import math
import sys

if (len(sys.argv) < 2):
	#inFile = "Sinusoid_147p461KHz_NomRefV_VDDA2p5_ADC_2M.txt"
	inFile = "temp_2M.txt"
else:
	inFile = sys.argv[1]

print("Input file name : ",inFile)
Codes16 = np.loadtxt(inFile,dtype=int)

#Codes16 = [0,0,1,2,3,4,5,6,7,8]
Codes12 = []
for CurrentCode in Codes16:
        Codes12.append(int(np.floor(CurrentCode/16)))

# the histogram of the data
#minbin = 150
#maxbin = 4000
### Remove lower and upper 30 codes near the boundaries
sortCodes12=np.sort(Codes12)
minbin = sortCodes12[30]
maxbin = sortCodes12[-30]
yoffset = ((sortCodes12[1]+sortCodes12[-2])/2)-2048.
print("Min/max code, spread (16bit)=",min(Codes16),max(Codes16),(max(Codes16)-min(Codes16)))
print("Min/max code, spread (12bit)=",min(Codes12),max(Codes12),(max(Codes12)-min(Codes12)))
print("Second Min/max code, offset (12bit)=",sortCodes12[1],sortCodes12[-2], yoffset)
del sortCodes12


