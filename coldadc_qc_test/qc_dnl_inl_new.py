#!/usr/bin/env python3

import os
import time
import binascii
import sys, os
import RPi.GPIO as GPIO
import spidev
import serial
import readADC_NSamp_new
import readCtrlReg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from scipy.optimize import curve_fit
import numpy as np
import math
from qc_linearity_sine_14bit import calc_linearity
from random import uniform

import pandas as pd

def getChADCVal(ADC_Data,chnum):
    adcArray=[]
    ichnum=chnum
    for iCnt in range (0,int((len(ADC_Data))/16)):
        adcArray.append(ADC_Data[ichnum])
        ichnum += 16
    return(adcArray)

def getADCVal(ADC_Data,adcNum):
    adcArray=[]
    ichNum=int(adcNum*8)
    for iCnt in range (0,int((len(ADC_Data))/16)):
        for iCh in range (0,8):
            adcArray.append(ADC_Data[ichNum])
            ichNum += 1
        ichNum += 8
    return(adcArray)


#######################################################################

def checkRegisters(serial0):
    Reg50Val=readCtrlReg.main(serial0,50)
    Reg9Val=readCtrlReg.main(serial0,9)
    if (( Reg50Val !=0) or (Reg9Val != 0 )):
        print("Error: register 9 and/or register 50 are NOT set to zero")
        sys.exit()

def printADCdata(iData):
    for iCnt in range (0,len(iData)):
        if ((iCnt%16) == 0 ):
            print("------------------------------------------------")
        print("Block",int(iCnt/16)," ADC Ch(",str(iCnt%16).zfill(2),") = ",hex(iData[iCnt]),
              " (",bin(iData[iCnt])[2:].zfill(16),")","(",iData[iCnt],")")
    return()

def calc_dnl_inl(dirsave=None, asicID=None, NumSet=480, deSerialData=None):


    if(dirsave==None):
        dirsave = os.environ.get("PWD")
        print(dirsave)
    if(asicID==None):
        asicID=''



    NChan = 16
    NWORDFIFO=65536

    #ColdADC synchronization. Find ADC channel 0
    ADC0Num=7
    #ADC0Num=readADC.findADCch0(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    #print("ADC0 Channel 0 = ",ADC0Num)

    #NumSet=1200  #2.5M samples for single channel read
    #NumSet=1
    ReadMode=2
    
    SampRate=1./2E6

    #Number of time step
    NTimeStp=int((NWORDFIFO/32)*NumSet)
    if ReadMode != 2:
        NTimeStp=int(NTimeStp*8)
        SampRate=1./16E6

    ix=np.zeros(16)
    y0 = np.zeros((16,NTimeStp))
    iadcVal=[]

    for iLoop in range(0,NumSet):

        for ch in range(0,16):
            ChNum = (ADC0Num+ch%8)%8 + 8*(ch//8)
        ######Single channel read mode
            if ReadMode == 2:
                iadcVal = getChADCVal(deSerialData[iLoop],ChNum)

            else:
            ######ADC Test Input Mode (ReadMode=ADC#)
                iadcVal = getADCVal(deSerialData[iLoop],ReadMode)

            for jx in range (0,len(iadcVal)):
     
                y0[ch][int(ix[ch])]=iadcVal[jx]
                ix[ch]+=1

        if (iLoop%10) == 0:
            print("Rearrange  # ",iLoop)

    del deSerialData

    outFile=open("{}/ColdADC_{}_dnl_inl.csv".format(dirsave,asicID),"w")    
    for ist in range(0,NTimeStp):
        iLine=f"{ist}"
        for ich in range(0,16):
            iLine=iLine+f", {y0[ich][ist]:.0f}"
        iLine=iLine+"\n"
        outFile.write(iLine)
    outFile.close()

    code=[[] for i in range(NChan)]
    dnl=[[] for i in range(NChan)]
    inlNorm=[[] for i in range(NChan)]
    midADCmean=[0 for i in range(NChan)]
    midADCstd=[0 for i in range(NChan)]
    xch = []
    max_d=[]
    min_d=[]
    std=[]
    max_i=[]
    min_i=[]
    Name=[]
    for ich in range (0, NChan):
        xch.append(ich)
        code[ich], dnl[ich], inlNorm[ich], midADCmean[ich], midADCstd[ich] = calc_linearity(y0[ich])

        
        arr=np.array(dnl[ich])
        arr_i=np.array(inlNorm[ich])
        max_d.append(np.max(arr))
        min_d.append(np.min(arr))
        std.append(np.std(arr))
        max_i.append(np.max(arr_i))
        min_i.append(np.min(arr_i))
        Name.append(ich)
    name_dict={
    'name':Name,
    'max_dnl':max_d,
    'min_dnl':min_d,
    'std_dnl':std,
    'max_inl':max_i,
    'min_ind':min_i
    }
    df=pd.DataFrame(name_dict)
    df.to_csv("{}/ColdADC_{}_dnl_inl_report.csv".format(dirsave,asicID))

    
    fig1, axs1 = plt.subplots(4,2)
    fig1.suptitle('DNL for All ADC0 Channels')
    fig1.set_size_inches(15,15)
    for ich in range(0,int(NChan/2)):
        col,row=0,0
        if ich<4:
            col = 0
            row = ich - col*4
            axs1[row, col].set_ylabel('DNL [LBS]')
        else:
            col = 1

        row = ich - col*4
        if row == 0:
            axs1[row, col].set_title('Channel {}'.format(int(ich+1)))
        elif row == 3:
            axs1[row, col].set_xlabel('ADC Code')
        axs1[row, col].plot(code[ich],dnl[ich])
    
    fig1.savefig("{}/ColdADC_{}_DNL_ADC0.png".format(dirsave,asicID))
#    plt.close()
    plt.clf()
    plt.close(fig1)


    fig2, axs2 = plt.subplots(4,2)
    fig2.suptitle('DNL for All ADC1 Channels')
    fig2.set_size_inches(15,15)
    for ich in range(0,int(NChan/2)):
        col,row=0,0
        if ich<4:
            col = 0
            row = ich - col*4
            axs2[row, col].set_ylabel('DNL [LBS]')
        else:
            col = 1

        row = ich - col*4
        if row == 0:
            axs2[row, col].set_title('Channel {}'.format(int(ich+9)))
        elif row == 3:
            axs2[row, col].set_xlabel('ADC Code')
        axs2[row, col].plot(code[ich+8],dnl[ich+8])
    fig2.savefig("{}/ColdADC_{}_DNL_ADC1.png".format(dirsave,asicID))
#    plt.close()
    plt.clf()
    plt.close(fig2)

    fig3, axs3 = plt.subplots(4,2)
    fig3.suptitle('INL for All ADC0 Channels')
    fig3.set_size_inches(15,15)
    for ich in range(0,int(NChan/2)):
        col,row=0,0
        if ich<4:
            col = 0
            row = ich - col*4
            axs3[row, col].set_ylabel('INL [LBS]')
        else:
            col = 1

        row = ich - col*4
        if row == 0:
            axs3[row, col].set_title('Channel {}'.format(int(ich+1)))
        elif row == 3:
            axs3[row, col].set_xlabel('ADC Code')
        axs3[row, col].plot(code[ich],inlNorm[ich])
    fig3.savefig("{}/ColdADC_{}_INL_ADC0.png".format(dirsave,asicID))
#    plt.close()
    plt.clf()
    plt.close(fig3)


    fig4, axs4 = plt.subplots(4,2)
    fig4.suptitle('INL for All ADC1 Channels')
    fig4.set_size_inches(15,15)
    for ich in range(0,int(NChan/2)):
        col,row=0,0
        if ich<4:
            col = 0
            row = ich - col*4
            axs4[row, col].set_ylabel('INL [LBS]')
        else:
            col = 1

        row = ich - col*4
        if row == 0:
            axs4[row, col].set_title('Channel {}'.format(int(ich+9)))
        elif row == 3:
            axs4[row, col].set_xlabel('ADC Code')
        axs4[row, col].plot(code[ich+8],inlNorm[ich+8])
    fig4.savefig("{}/ColdADC_{}_INL_ADC1.png".format(dirsave,asicID))
#    plt.close()
    plt.clf()
    plt.close(fig4)

    fig=plt.figure()
    plt.plot(xch, midADCstd,'.')
    plt.ylim([0,50])
    plt.xlabel("Channel")
    plt.ylabel("Mid Occupancy StD  [ADC]")
    plt.savefig("{}/ColdADC_{}_Occup_StD.png".format(dirsave,asicID))
    plt.clf()
    plt.close()


    status = True

#    plt.show()


    #Close output file
    #outFile.close()
      
    return status

if __name__ == '__main__':

    FPGA_FIFO_FULL=12
    UART_SEL=27
    ADC_RESET=6
    FPGA_RESET=22

    NWORDFIFO=65536
    NSamples = 80
 
    spi = readADC_NSamp_new.initSPI()
    gport = readADC_NSamp_new.initGPIOpoll(FPGA_FIFO_FULL)
    rawdata = readADC_NSamp_new.readNSamp(gport,spi,FPGA_FIFO_FULL,NWORDFIFO,NSamples)

    spi.close()
    gport.cleanup

    deserLinData = []
    for i in range(len(rawdata)):
        firstBlock=rawdata[i][0:NWORDFIFO]
        #Deserialize ADC data
        deserLinData.append (readADC_NSamp_new.deSerialize(firstBlock) )
        if (i%10) == 0:
            print("Deserialize Sample # ",i)
#        printFPGAfifo(firstBlock)
    del rawdata


    if(len(sys.argv)==3):
        dirsave = sys.argv[1]
        asicID = sys.argv[2]
        print(dirsave,asicID)
        calc_dnl_inl(dirsave,asicID,NSamples,deserLinData)
    else:
        calc_dnl_inl(None,None,NSamples,deserLinData)

    
