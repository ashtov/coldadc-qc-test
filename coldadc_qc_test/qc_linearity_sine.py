#!/usr/bin/env python3
""" Calculates INL and DNL from sine wave data. Adjust minbin and maxbin
    depending on your data.
    Ported from MATLAB to Python by C. Grace (crgrace@lbl.gov)
    Original MATLAB (dnl_inl_sin.m) by Boris Murmann (Aug 2002)
"""

import numpy as np
import matplotlib.pyplot as plt
import math
import sys

def calc_linearity(Codes16):
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
#    print("Min/max code, spread (16bit)=",min(Codes16),max(Codes16),(max(Codes16)-min(Codes16)))
#    print("Min/max code, spread (12bit)=",min(Codes12),max(Codes12),(max(Codes12)-min(Codes12)))
#    print("Second Min/max code, offset (12bit)=",sortCodes12[1],sortCodes12[-2], yoffset)
    del sortCodes12
    
    # histogram in numpy returns bin edges, but hisogram in matlab uses 
    # bin centers
    # to simplify calculations use bin centers, so we calculate edges to get
    # the centers that we want
    bins = []
    for myBin in range(minbin,maxbin+2):
        bins.append(myBin - 0.5)   # bin center
        # add extra binedges to capture values above and below final edges
    bins.append(4096.5)    
    bins = np.insert(bins,0,0.0)
#    print(bins)  
  
    # find histrogram
    h,binedges = np.histogram(Codes12,bins)
#    print(h)   
    plt.hist(Codes12,bins)
    plt.title("1M Samples Occupancy")
    plt.xlabel("ADC Code (12 bit)")
    plt.show()
    plt.savefig("dnl_occupancy.png")

    # cumulative historgram
    ch = np.cumsum(h)
    
    # find transition levels
    histosum = np.sum(h)
    T = []
    for CurrentLevel in range(np.size(ch)):
        #print(CurrentLevel)
        T.append(-math.cos(math.pi*ch[CurrentLevel]/histosum))
    
    # linearized historgram
    end = np.size(T)
    hlin = []
    hlin = np.subtract(T[1:end],T[0:end-1])
    
    # truncate at least first and last bin, more if input did not clip ADC
    trunc = 10
    hlin_trunc = hlin[trunc:np.size(hlin)-trunc]
    
    # calculate LSB size and DNL
    lsb = np.sum(hlin_trunc) / np.size(hlin_trunc)
    dnl = 0
    dnl = [hlin_trunc/lsb-1]
    # define 0th DNL value as 0
    dnl = np.insert(dnl,0,0.0)
    # calculate inl
    inl = np.cumsum(dnl)
    #normalize inl plot
    inlNorm=inl-(np.mean(inl))
    
    code = np.linspace(minbin+trunc,maxbin-trunc,np.size(dnl))
    # convert to int
    code = code.astype(int)

    return code, dnl, inlNorm
    
if __name__ == '__main__':

    if (len(sys.argv) < 2):
	#inFile = "Sinusoid_147p461KHz_NomRefV_VDDA2p5_ADC_2M.txt"
        inFile = "temp_2M.txt"
    else:
        inFile = sys.argv[1]

    print("Input file name : ",inFile)
    Codes16 = np.loadtxt(inFile,dtype=int)

    #Codes16 = [0,0,1,2,3,4,5,6,7,8]

    code, dnl, inlNorm = calc_linearity(Codes16)

    # make plots
    plt.gcf().clear()
    fig = plt.figure(1)
    dnl_axes = fig.add_subplot(211)
    dnl_axes.plot(code,dnl)

    plt.ylabel('DNL [LSB]')
    #dnl_axes.set_title(r'CMOS Reference, 16MHzADC-Clk, LN2 ($f_{in}$=147 kHz)')
    dnl_axes.set_title(r'ColdADC Static Linearity ($f_{in}$=147 kHz, $V_{p-p}$=1.4V)')
    #dnl_axes.set_title(r'ColdADC Static Linearity ($f_{in}$=147 kHz, LN2)')
    #dnl_axes.set_title(r'ColdADC Static Linearity in Faraday Cage at RT ($f_{in}$=20.5 kHz, $V_{p-p}$=1.4V)')
    #dnl_axes.set_title(r'CMOS VREFP/N $\mp$300mV, ADC Bias 10$\mu$A, 1MHzADC-Clk, ($f_{in}$=21 kHz)')
    dnl_axes.set_autoscaley_on(True)
    #dnl_axes.set_ylim([-0.5,0.5])

    inl_axes = fig.add_subplot(212)
    inl_axes.plot(code,inlNorm)
    plt.xlabel('ADC Code')
    plt.ylabel('INL [LSB]')
    inl_axes.set_autoscaley_on(True)
    #inl_axes.set_ylim([-1.0,1.5])
    plt.show

    #plt.savefig('cold_adc_static_linearity.png',format='png',dpi=300)
    plt.savefig('temp.png',format='png',dpi=300)
    
