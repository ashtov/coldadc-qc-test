#!/usr/bin/env python3

import os
import time
import binascii
import sys, os
import RPi.GPIO as GPIO
import spidev
import serial
import readADC_NSamp
import readCtrlReg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from scipy.optimize import curve_fit
import numpy as np
import math
from qc_linearity_sine_14bit import calc_linearity
from random import uniform


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




def calc_dnl_inl(dirsave=None, asicID=None):


    if(dirsave==None):
        dirsave = os.environ.get("PWD")
        print(dirsave)
    if(asicID==None):
        asicID=''


    ser = serial.Serial(
                port='/dev/serial0',
                baudrate=1000000,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS)

    print (ser.portstr)

    #Clear Serial buffers
    ser.flush()
    #ser.flushInput()
    #ser.flushOutput()

    #Configure spi0
    spi0 = spidev.SpiDev()
    spi0.open(0,0)
    spi0.max_speed_hz = 8000000
    #mode [CPOL][CPHA]: 0b01=latch on trailing edge of clock
    spi0.mode = 0b01
    
    #Configure GPIO
    GPIO.setmode(GPIO.BCM)
    #GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    #Define GPIO pins
    FPGA_FIFO_FULL=12
    UART_SEL=27
    ADC_RESET=6
    FPGA_RESET=22

    #Set input and output pins
    GPIO.setup(FPGA_FIFO_FULL, GPIO.IN)
    GPIO.setup(UART_SEL, GPIO.OUT)
    GPIO.setup(FPGA_RESET, GPIO.OUT)
    GPIO.setup(ADC_RESET, GPIO.OUT)

    #Set output pin initial state
#    GPIO.output(UART_SEL, GPIO.HIGH)
    GPIO.output(FPGA_RESET, GPIO.HIGH)
    GPIO.output(ADC_RESET, GPIO.HIGH)
    time.sleep(0.1)

    NChan = 16
    #Open output file
    #outFile=open("Sinusoid_66KHz_ReducedVRef_2MSamples.txt","w")
    #outFile=open("Sinusoid_11p2304KHz_NomRefV_VDDA2p5_SingleEnded-SHA-ADC_2M.txt","w")
    #outFile=open("Sinusoid_20p5078KHz_NomRefV_VDDA2p5_singleEnded-SHA-ADC_2M.txt","w")
    #outFile=open("Sinusoid_11p2304KHz_NomRefV_VDDA2p5_SDC-SHA-ADC_2M.txt","w")
    #outFile=open("Sinusoid_147p461KHz_NomRefV_VDDA2p5_ADC_2M.txt","w")
    #outFile=open("Sinusoid_147p461KHz_VREFPN-200mV_VDDA2p25_Reg23-0x30_ADC_2M.txt","w")
    #outFile=open("Sinusoid_147p461KHz_NomVREFPN_VDDA2p35_ADC_2M.txt","w")
    #outFile=open("Sinusoid_17KHz_NomRefV_VDDA2p5_ADC_2M.txt","w")
    #outFile=open("temp_2M.txt","w")

    #readADC.resetCHIP(GPIO, FPGA_RESET)
    #readADC.resetCHIP(GPIO, ADC_RESET)

    #Number of words in FPGA FIFO
    NWORDFIFO=65536

    #ColdADC synchronization. Find ADC channel 0
    ADC0Num=7
    #ADC0Num=readADC.findADCch0(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    #print("ADC0 Channel 0 = ",ADC0Num)

    #Verify both registers 9 and 50 are set to 0
    #checkRegisters(ser)

    # For ADC Test input only NumSet=120 --> 2M samples
    # For Full chain reading out one channel need NumSet=960 to get 2M samples
    #NumSet=80   #4M samples for ADC test mode
    NumSet=480  #1M samples for single channel read
    #NumSet=1200  #2.5M samples for single channel read
    #NumSet=1
    
    ##############################################
    #Readout Mode (0=read ADC0 block, 1=read ADC1 block, 2=single channel read)
    #             ChNum ignored if ReadMode<2
    ##############################################
    ReadMode=2

    #ChNum = (ADC0Num+0)%8  # ADC0

    SampRate=1./2E6

    #Number of time step
    NTimeStp=int((NWORDFIFO/32)*NumSet)
    if ReadMode != 2:
        NTimeStp=int(NTimeStp*8)
        SampRate=1./16E6

    ix=np.zeros(16)
    y0 = np.zeros((16,NTimeStp))
    iadcVal=[]

    timeStamp = time.process_time()
    rawtime = time.time()
    deSerialData=readADC_NSamp.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO, NumSet)
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
    #print(str(time.process_time() - timeStamp) + " seconds for data reading")
    #print(str(time.time() - rawtime) + " raw seconds for data reading")

    timeStamp = time.process_time()
    rawtime = time.time()
    outFile=open("{}/ColdADC_{}_dnl_inl.csv".format(dirsave,asicID),"w")    
    for ist in range(0,NTimeStp):
        iLine=f"{ist}"
        for ich in range(0,16):
            iLine=iLine+f", {y0[ich][ist]:.0f}"
        iLine=iLine+"\n"
        outFile.write(iLine)
    outFile.close()
    #print(str(time.process_time() - timeStamp) + " seconds for CSV writing")
    #print(str(time.time() - rawtime) + " raw seconds for CSV writing")

    timeStamp = time.process_time()
    rawtime = time.time()
    code=[[] for i in range(NChan)]
    dnl=[[] for i in range(NChan)]
    inlNorm=[[] for i in range(NChan)]
    midADCmean=[0 for i in range(NChan)]
    midADCstd=[0 for i in range(NChan)]
    xch = []
    for ich in range (0, NChan):
        xch.append(ich)
        code[ich], dnl[ich], inlNorm[ich], midADCmean[ich], midADCstd[ich] = calc_linearity(y0[ich])


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

    fig=plt.figure()
    plt.plot(xch, midADCstd,'.')
    plt.ylim([0,50])
    plt.xlabel("Channel")
    plt.ylabel("Mid Occupancy StD  [ADC]")
    plt.savefig("{}/ColdADC_{}_Occup_StD.png".format(dirsave,asicID))

    #print(str(time.process_time() - timeStamp) + " seconds for plot generation")
    #print(str(time.time() - rawtime) + " raw seconds for plot generation")
    status = True

#    plt.show()


    #Exit GPIO cleanly
    GPIO.cleanup

    #Close serial port
    ser.close()

    #Close spi0
    spi0.close()

    #Close output file
    #outFile.close()
      
    return status

if __name__ == '__main__':

    if(len(sys.argv)==3):
        dirsave = sys.argv[1]
        asicID = sys.argv[2]
        print(dirsave,asicID)
        calc_dnl_inl(dirsave,asicID)
    else:
        calc_dnl_inl()



       



