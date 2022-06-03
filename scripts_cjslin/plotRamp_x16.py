#!/usr/bin/env python3

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
import numpy as np

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



if __name__ == '__main__':

#    if (len(sys.argv) != 3):
#        print("\readADC.py requires 2 arguments: address (int) and value (int,0x,0b)")
#        print("Example:  ./coldADC_writeCtrlReg.py 31 0b100 \n")
#        sys.exit()
    
#    #Set register address (config bit is already set to 1)
#    iAddress=int(sys.argv[1])
#    idata=sys.argv[2]

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
    GPIO.output(UART_SEL, GPIO.HIGH)
    GPIO.output(FPGA_RESET, GPIO.HIGH)
    GPIO.output(ADC_RESET, GPIO.HIGH)
    time.sleep(0.1)

    #Open output file
    #outFile=open("Sinusoid_66KHz_ReducedVRef_2MSamples.txt","w")
    #outFile=open("Sinusoid_152p343KHz_FFT_NomRefV_VVDA2p5.txt","w")
    outFile=open("test.txt","w")

    #readADC.resetCHIP(GPIO, FPGA_RESET)
    #readADC.resetCHIP(GPIO, ADC_RESET)

    #Number of words in FPGA FIFO
    NWORDFIFO=65536

    #ColdADC synchronization. Find ADC channel 0
    ADC0Num=5
    #ADC0Num=readADC.findADCch0(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    #print("ADC0 Channel 0 = ",ADC0Num)

    #Verify both registers 9 and 50 are set to 0
    #checkRegisters(ser)

    NumSet=1
    
    ##############################################
    #Readout Mode (0=read ADC0 block, 1=read ADC1 block, 2=single channel read)
    #             ChNum ignored if ReadMode<2
    ##############################################
    ReadMode=2
    ChNum = 6
    SampRate=1./2E6

    #Number of time step
    NTimeStp=int((NWORDFIFO/32)*NumSet)
    if ReadMode != 2:
        NTimeStp=int(NTimeStp*8)
        SampRate=1./16E6

    x0 = np.zeros(NTimeStp)
    x0.astype(float)
    y0 = np.zeros(NTimeStp)
    y1 = np.zeros(NTimeStp)
    y2 = np.zeros(NTimeStp)
    y3 = np.zeros(NTimeStp)
    y4 = np.zeros(NTimeStp)
    y5 = np.zeros(NTimeStp)
    y6 = np.zeros(NTimeStp)
    y7 = np.zeros(NTimeStp)
    y8 = np.zeros(NTimeStp)
    y9 = np.zeros(NTimeStp)
    y10 = np.zeros(NTimeStp)
    y11 = np.zeros(NTimeStp)
    y12 = np.zeros(NTimeStp)
    y13 = np.zeros(NTimeStp)
    y14 = np.zeros(NTimeStp)
    y15 = np.zeros(NTimeStp)

    
    ix = 0
    iadc0Val=[]
    iadc1Val=[]
    iadc2Val=[]
    iadc3Val=[]
    iadc4Val=[]
    iadc5Val=[]
    iadc6Val=[]
    iadc7Val=[]
    iadc8Val=[]
    iadc9Val=[]
    iadc10Val=[]
    iadc11Val=[]
    iadc12Val=[]
    iadc13Val=[]
    iadc14Val=[]
    iadc15Val=[]
    idummy=readADC.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    for iLoop in range(0,NumSet):
        deSerialData=readADC.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
        ######Single channel read mode
        if ReadMode == 2:
            iadc0Val = getChADCVal(deSerialData,0)
            iadc1Val = getChADCVal(deSerialData,1)
            iadc2Val = getChADCVal(deSerialData,2)
            iadc3Val = getChADCVal(deSerialData,3)
            iadc4Val = getChADCVal(deSerialData,4)
            iadc5Val = getChADCVal(deSerialData,5)
            iadc6Val = getChADCVal(deSerialData,6)
            iadc7Val = getChADCVal(deSerialData,7)
            iadc8Val = getChADCVal(deSerialData,8)
            iadc9Val = getChADCVal(deSerialData,9)
            iadc10Val = getChADCVal(deSerialData,10)
            iadc11Val = getChADCVal(deSerialData,11)
            iadc12Val = getChADCVal(deSerialData,12)
            iadc13Val = getChADCVal(deSerialData,13)
            iadc14Val = getChADCVal(deSerialData,14)
            iadc15Val = getChADCVal(deSerialData,15)
        else:
        ######ADC Test Input Mode (ReadMode=ADC#)
            iadc0Val = getADCVal(deSerialData,ReadMode)


        #y0 += iadcVal
        for jx in range (0,len(iadc0Val)):
            x0[ix]=float(ix)*SampRate  
            y0[ix]=iadc0Val[jx]
            y1[ix]=iadc1Val[jx]
            y2[ix]=iadc2Val[jx]
            y3[ix]=iadc3Val[jx]
            y4[ix]=iadc4Val[jx]
            y5[ix]=iadc5Val[jx]
            y6[ix]=iadc6Val[jx]
            y7[ix]=iadc7Val[jx]
            y8[ix]=iadc8Val[jx]
            y9[ix]=iadc9Val[jx]
            y10[ix]=iadc10Val[jx]
            y11[ix]=iadc11Val[jx]
            y12[ix]=iadc12Val[jx]
            y13[ix]=iadc13Val[jx]
            y14[ix]=iadc14Val[jx]
            y15[ix]=iadc15Val[jx]
                        
            ix += 1


    # create the function we want to fit
    def my_sin(x, freq, amplitude, phase, offset):
        return np.sin(x * freq + phase) * amplitude + offset

    #guess_freq = 152343.0 * (2.0*np.pi)
    guess_freq = 30343.0 * (2.0*np.pi)
    guess_amplitude = (y0.max()-y0.min())/2.0
    guess_phase = 0
    guess_offset = np.mean(y0)


    #Setup plot
    #style.use('fivethirtyeight')
    fig = plt.figure()
    ax1 = fig.add_subplot(4,2,1)
    #plt.xlabel('Time (Sec)')
    plt.ylabel('ADC Count')
    plt.title('SHA#0')
    ax1.plot(x0,y0,'.',label='ADC Output')

    ax2 = fig.add_subplot(4,2,2)
    #plt.xlabel('Time (Sec)')
    #plt.ylabel('ADC Count')
    plt.title('SHA#1')
    ax2.plot(x0,y1,'.')

    ax3 = fig.add_subplot(4,2,3)
    #plt.xlabel('Time (Sec)')
    plt.ylabel('ADC Count')
    plt.title('SHA#2')
    ax3.plot(x0,y2,'.')

    ax4 = fig.add_subplot(4,2,4)
    #plt.xlabel('Time (Sec)')
    #plt.ylabel('ADC Count')
    plt.title('SHA#3')
    ax4.plot(x0,y3,'.')

    ax5 = fig.add_subplot(4,2,5)
    #plt.xlabel('Time (Sec)')
    plt.ylabel('ADC Count')
    plt.title('SHA#4')
    ax5.plot(x0,y4,'.')

    ax6 = fig.add_subplot(4,2,6)
    #plt.xlabel('Time (Sec)')
    #plt.ylabel('ADC Count')
    plt.title('SHA#5')
    ax6.plot(x0,y5,'.')

    ax7 = fig.add_subplot(4,2,7)
    plt.xlabel('Time (Sec)')
    plt.ylabel('ADC Count')
    plt.title('SHA#6')
    ax7.plot(x0,y6,'.')

    ax8 = fig.add_subplot(4,2,8)
    plt.xlabel('Time (Sec)')
    #plt.ylabel('ADC Count')
    plt.title('SHA#7')
    ax8.plot(x0,y7,'.')

    
    #plt.show()

    fig2 = plt.figure()
    ax1b = fig2.add_subplot(4,2,1)
    #plt.xlabel('Time (Sec)')
    plt.ylabel('ADC Count')
    plt.title('SHA#8')
    ax1b.plot(x0,y8,'.',label='ADC Output')

    ax2b = fig2.add_subplot(4,2,2)
    #plt.xlabel('Time (Sec)')
    #plt.ylabel('ADC Count')
    plt.title('SHA#9')
    ax2b.plot(x0,y9,'.')

    ax3b = fig2.add_subplot(4,2,3)
    #plt.xlabel('Time (Sec)')
    plt.ylabel('ADC Count')
    plt.title('SHA#10')
    ax3b.plot(x0,y10,'.')

    ax4b = fig2.add_subplot(4,2,4)
    #plt.xlabel('Time (Sec)')
    #plt.ylabel('ADC Count')
    plt.title('SHA#11')
    ax4b.plot(x0,y11,'.')

    ax5b = fig2.add_subplot(4,2,5)
    #plt.xlabel('Time (Sec)')
    plt.ylabel('ADC Count')
    plt.title('SHA#12')
    ax5b.plot(x0,y12,'.')

    ax6b = fig2.add_subplot(4,2,6)
    #plt.xlabel('Time (Sec)')
    #plt.ylabel('ADC Count')
    plt.title('SHA#13')
    ax6b.plot(x0,y13,'.')

    ax7b = fig2.add_subplot(4,2,7)
    plt.xlabel('Time (Sec)')
    plt.ylabel('ADC Count')
    plt.title('SHA#14')
    ax7b.plot(x0,y14,'.')

    ax8b = fig2.add_subplot(4,2,8)
    plt.xlabel('Time (Sec)')
    #plt.ylabel('ADC Count')
    plt.title('SHA#15')
    ax8b.plot(x0,y15,'.')

    
    plt.show()


    #Exit GPIO cleanly
    GPIO.cleanup

    #Close serial port
    ser.close()

    #Close spi0
    spi0.close()

    #Close output file
    outFile.close()
