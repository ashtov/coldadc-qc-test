#!/usr/bin/env python3

import os
import time
import binascii
import sys
import RPi.GPIO as GPIO
import spidev
import serial
import readADC
import readCtrlReg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from scipy.optimize import curve_fit
from scipy.stats import norm
import numpy as np
import fft_test_v2 as fft

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



#if __name__ == '__main__':

def calc_fft(dirsave=None, asicID=None):
#    if (len(sys.argv) != 3):
#        print("\readADC.py requires 2 arguments: address (int) and value (int,0x,0b)")
#        print("Example:  ./coldADC_writeCtrlReg.py 31 0b100 \n")
#        sys.exit()
    
#    #Set register address (config bit is already set to 1)
#    iAddress=int(sys.argv[1])
#    idata=sys.argv[2]

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

    #Open output file
    #outFile=open("Sinusoid_66KHz_ReducedVRef_2MSamples.txt","w")
    #outFile=open("Sinusoid_152p343KHz_FFT_NomRefV_VVDA2p5.txt","w")
    outFile=open("{}/ColdADC_{}_harmonic_data.csv".format(dirsave,asicID),"w")

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
    NChan=int(16)
    NumSet=5
    
    ##############################################
    #Readout Mode (0=read ADC0 block, 1=read ADC1 block, 2=single channel read)
    #             ChNum ignored if ReadMode<2
    ##############################################
    ReadMode=2
#    ChNum = (ADC0Num+0)%8 # ADC0
    SampRate=1./2E6

    #Number of time step
    NTimeStp=int((NWORDFIFO/32))#*NumSet)
    if ReadMode != 2:
        NTimeStp=int(NTimeStp*8)
        SampRate=1./16E6

    x0 = np.zeros((NumSet,NTimeStp))
#    print (len(x0[0]))
    x0.astype(float)
    y = np.zeros(((NumSet, NChan, NTimeStp)))

    ix = 0
    iadcVal=[[[] for i in range(NChan)] for j in range(NumSet)]

    idummy=readADC.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    for iLoop in range(0,NumSet):
        deSerialData=readADC.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
        ######Single channel read mode
        if ReadMode == 2:
            for ich in range(0, NChan):
                ChNum = (ADC0Num+ich%8)%8 + 8*(ich//8)
                iadcVal[iLoop][ich] = getChADCVal(deSerialData,ChNum)
                

        else:
        ######ADC Test Input Mode (ReadMode=ADC#)
            iadcVal[iLoop][0] = getADCVal(deSerialData,ReadMode)


        #y0 += iadcVal
       
        for jx in range (0,len(iadcVal[iLoop][0])):
            x0[iLoop][jx]=float(ix)*SampRate
            for ich in range(0, NChan):  
                y[iLoop][ich][jx]=iadcVal[iLoop][ich][jx]
                        
            ix += 1

    for iLoop in range(0,NumSet):

#        print(len(x0[iLoop]))
        for ilin in range (0, len(x0[iLoop])):
            iLine=f"{x0[iLoop][ilin]:.5e}"
#        outFile.write(f"{x0[ilin]:.5e}, {y1[ilin]:.1f}, {y2[ilin]:.1f}, {y3[ilin]:.1f}, {y4[ilin]:.1f}, {y5[ilin]:.1f}, {y6[ilin]:.1f}, {y7[ilin]:.1f}, {y8[ilin]:.1f}, {y9[ilin]:.1f}, {y10[ilin]:.1f}, {y11[ilin]:.1f}, {y12[ilin]:.1f}, {y13[ilin]:.1f}, {y14[ilin]:.1f}, {y15[ilin]:.1f}\n")
            for ich in range(0, NChan):
                iLine=iLine+f", {y[iLoop][ich][ilin]:.1f}"
            iLine=iLine+"\n" 
            outFile.write(iLine)
    outFile.close()

    fig1, axs1 = plt.subplots(4,2)
    fig1.suptitle('Channels for ADC0')
    fig1.set_size_inches(15,15)
    for ich in range(0,int(NChan/2)):
        col,row=0,0
        if ich<4:   
            col = 0
            row = ich - col*4
            axs1[row, col].set_ylabel('ADC Count')
        else:
            col = 1
       
        row = ich - col*4
        if row == 0:       
            axs1[row, col].set_title('Channel {}'.format(int(ich+1)))
        elif row == 3:
            axs1[row, col].set_xlabel('Sample Time [s]')
        axs1[row, col].plot(x0[0],y[0][ich],'.')
    fig1.savefig("{}/ColdADC_{}_data_ADC0.png".format(dirsave,asicID))
    plt.close()


    fig2, axs2 = plt.subplots(4,2)
    fig2.suptitle('Channels for ADC1')
    fig2.set_size_inches(15,15)
    for ich in range(0,int(NChan/2)):
        col,row=0,0
        if ich<4:
            col = 0
            row = ich - col*4
            axs2[row, col].set_ylabel('ADC Count')
        else:
            col = 1

        row = ich - col*4
        if row == 0:
            axs2[row, col].set_title('Channel {}'.format(int(ich+9)))
        elif row == 3:
            axs2[row, col].set_xlabel('Sample Time [s]')
        axs2[row, col].plot(x0[0],y[0][ich+8],'.')
    fig2.savefig("{}/ColdADC_{}_data_ADC1.png".format(dirsave,asicID))  
    plt.close()
    
    #plt.show()
    figfft=plt.figure()

    fft_out=[]
    sndr=[[]for j in range(NumSet)]
    enob=[[]for j in range(NumSet)]
    snr=[[]for j in range(NumSet)]
    sfdr=[[]for j in range(NumSet)]
    thd=[[]for j in range(NumSet)]
    xch=[[]for j in range(NumSet)]
    freqs=[[[]for i in range(NChan)]for j in range(NumSet)]
    xdb=[[[]for i in range(NChan)]for j in range(NumSet)]
    window = np.hanning(2048)
    for iLoop in range(0,NumSet):
        for ich in range(0,NChan):
            fft_out=fft.AnalyzeDynamicADC(y[iLoop][ich],2048,16,2,window)
#        print(fft_out[1],"\n")
            xch[iLoop].append(ich)
            sndr[iLoop].append(fft_out[0])
            enob[iLoop].append(fft_out[1])
            snr[iLoop].append(fft_out[2])
            sfdr[iLoop].append(fft_out[3])
            thd[iLoop].append(fft_out[4])
            freqs[iLoop][ich]=fft_out[5]
            xdb[iLoop][ich]=fft_out[6]
    plt.close()

    outFile=open("{}/ColdADC_{}_dynamic.csv".format(dirsave,asicID),"w")

    for iLoop in range(0,NumSet):
        for ich in range(0,len(sndr[iLoop])):
            outFile.write (f"{xch[iLoop][ich]}, {sndr[iLoop][ich]:.1f}, {enob[iLoop][ich]:.1f}, {snr[iLoop][ich]:.1f}, {sfdr[iLoop][ich]:.1f}, {thd[iLoop][ich]:.1f} \n")
    outFile.close()

    xdb_avg = np.zeros((NChan, len(freqs[iLoop][ich])))

    for ich in range(0,len(sndr[0])):
        for iLoop in range(0,NumSet):
            for ifreq in range (0,len(freqs[iLoop][ich])):
                xdb_avg[ich][ifreq]=xdb_avg[ich][ifreq]+xdb[iLoop][ich][ifreq]/NumSet  
##            print(freqs[iLoop][ifreq],xdb[iLoop][ifreq])

    outFile=open("{}/ColdADC_{}_5SampleAve_fft.csv".format(dirsave,asicID),"w")
    for ich in range(0,len(sndr[0])):
        for ifreq in range (0,len(freqs[0][ich])):
            outFile.write(f"{ich}, {freqs[0][ich][ifreq]:.6f}, {xdb_avg[ich][ifreq]:.2f} \n")
    outFile.close()

    fig3, axs3 = plt.subplots(4,2)
    fig3.suptitle('Channels for ADC0')
    fig3.set_size_inches(15,15)
    for ich in range(0,int(NChan/2)):
        col,row=0,0
        if ich<4:
            col = 0
            row = ich - col*4
            axs3[row, col].set_ylabel('Amplitude [dBFS]')
        else:
            col = 1

        row = ich - col*4
        if row == 0:
            axs3[row, col].set_title('Channel {}'.format(int(ich+1)))
        elif row == 3:
            axs3[row, col].set_xlabel('Frequency [MHz]')
        axs3[row, col].plot(freqs[0][ich],xdb_avg[ich])
    fig3.savefig("{}/ColdADC_{}_FFT_ADC0.png".format(dirsave,asicID)) 
#    plt.close()   

    fig4, axs4 = plt.subplots(4,2)
    fig4.suptitle('Channels for ADC1')
    fig4.set_size_inches(15,15)
    for ich in range(0,int(NChan/2)):
        col,row=0,0
        if ich<4:
            col = 0
            row = ich - col*4
            axs4[row, col].set_ylabel('Amplitude [dBFS]')
        else:
            col = 1

        row = ich - col*4
        if row == 0:
            axs4[row, col].set_title('Channel {}'.format(int(ich+9)))
        elif row == 3:
            axs4[row, col].set_xlabel('Frequency [MHz]')
        axs4[row, col].plot(freqs[0][ich+8],xdb_avg[ich+8])
    fig4.savefig("{}/ColdADC_{}_FFT_ADC1.png".format(dirsave,asicID))
#    plt.close()

    fig5, axs5 = plt.subplots(3,2)
    fig5.suptitle('All Channels')
    fig5.set_size_inches(15,15)
    axs5[0,0].plot(xch[0],sndr[0],'.')
    axs5[0,0].set_ylim([0,100])
    axs5[0,0].set_ylabel('SNDR [dB]')
    axs5[1,0].plot(xch[0],enob[0],'.')
    axs5[1,0].set_ylim([0,16])
    axs5[1,0].set_ylabel('ENOB [bit]')
    axs5[2,0].plot(xch[0],snr[0],'.')
    axs5[2,0].set_ylim([0,80])
    axs5[2,0].set_ylabel('SNR [dB]')
    axs5[2,0].set_xlabel('Channel')
    axs5[0,1].plot(xch[0],sfdr[0],'.')
    axs5[0,1].set_ylim([0,100])
    axs5[0,1].set_ylabel('SFDR [dB]')
    axs5[1,1].plot(xch[0],thd[0],'.')
    axs5[1,1].set_ylabel('THD [dB]')
    axs5[1,1].set_ylim([-120,0])
    axs5[1,1].set_xlabel('Channel')
    axs5[2,1].set_axis_off()

    fig5.savefig("{}/ColdADC_{}_Dynamic.png".format(dirsave,asicID))
#    plt.close()
    plt.show()

    status = True

    #Exit GPIO cleanly
    GPIO.cleanup

    #Close serial port
    ser.close()

    #Close spi0
    spi0.close()

    #Close output file
#    outFile.close()

#    return sndr[0], enob[0], snr[0], sfdr[0], thd[0]

    return status

if __name__ == '__main__':

    if(len(sys.argv)==3):
        dirsave = sys.argv[1]
        asicID = sys.argv[2]
        print(dirsave,asicID)
        calc_fft(dirsave,asicID)
    else:
        calc_fft()

