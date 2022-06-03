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
from scipy.stats import norm
import numpy as np
import fft_test as fft

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
    #outFile=open("Sinusoid_147p461KHz_FFT_NomRefV_VVDA2p1_LN2.txt","w")
    #outFile=open("Sinusoid_20p5078KHz_FFT_singleEnded-SHA-ADC_NomRefV_VVDA2p5_VDDD2p5_LN2.txt","w")
    #outFile=open("Noise-ADC-TestInputs_NomRefV_VVDA2p5_RoomTemp.txt","w")
    outFile=open("test.txt","w")

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

    NumSet=1
    
    ##############################################
    #Readout Mode (0=read ADC0 block, 1=read ADC1 block, 2=single channel read)
    #             ChNum ignored if ReadMode!=2
    #NoiseStudy = 0  (0=data mode; 1= noise study)
    ##############################################
    ReadMode=2
    NoiseStudy = 0
    ChNum = (ADC0Num+6)%8  # ADC0
    #ChNum = (ADC0Num+0)%8 + 8 # ADC1
    SampRate=1./2E6

    #Number of time step
    NTimeStp=int((NWORDFIFO/32)*NumSet)
    if ReadMode != 2:
        NTimeStp=int(NTimeStp*8)
        SampRate=1./16E6

    x0 = np.zeros(NTimeStp)
    x0.astype(float)
    y0 = np.zeros(NTimeStp)


    ix = 0
    iadcVal=[]
    idummy=readADC.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    for iLoop in range(0,NumSet):
        deSerialData=readADC.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
        ######Single channel read mode
        if ReadMode == 2:
            iadcVal = getChADCVal(deSerialData,ChNum)
        else:
        ######ADC Test Input Mode (ReadMode=ADC#)
            iadcVal = getADCVal(deSerialData,ReadMode)

        print("Length of iadcVal = ",len(iadcVal))
        
        #y0 += iadcVal
        for jx in range (0,len(iadcVal)):
            x0[ix]=float(ix)*SampRate  
            y0[ix]=iadcVal[jx]
            #iLine=str(x0[ix])+","+str(iadcVal[jx])+"\n"
            iLine=str(iadcVal[jx])+"\n"
            outFile.write(iLine)
            ix += 1


    # create the function we want to fit
    def my_sin(x, freq, amplitude, phase, offset):
        return np.sin(x * freq + phase) * amplitude + offset

    def my_lin(x,slope,offset):
        return slope*x+offset
    
    guess_freq = 147460.0 * (2.0*np.pi)   # ADC only FFT
    #guess_freq = 20507.8 * (2.0*np.pi)     # Single Channel Full-Chain FFT

    guess_amplitude = (y0.max()-y0.min())/2.0
    guess_phase = 0
    guess_offset = np.mean(y0)
    guess_slope = 1.0
    
    print("Max, Min , offset ADC =",y0.max(), y0.min(), (y0.max()+y0.min())/2.-32768. )

    #Setup plot
    #style.use('fivethirtyeight')
    fig = plt.figure()
    if NoiseStudy == 0 :

        #p0=[guess_freq, guess_amplitude, guess_phase, guess_offset]
        p0=[guess_slope, guess_offset]

        # now do the fit
        #fit = curve_fit(my_sin, x0, y0, p0=p0)
        fit = curve_fit(my_lin, x0, y0, p0=p0)

        # we'll use this to plot our first estimate. 
        #data_first_guess = my_sin(x0, *p0)
        data_first_guess = my_lin(x0, *p0)

        # recreate the fitted curve using the optimized parameters
        #data_fit = my_sin(x0, *fit[0])
        data_fit = my_lin(x0, *fit[0])

        # residual (data - fit)
        residual = y0 - data_fit
        print("Max, min residuals = ",residual.max(),residual.min())

        ax1 = fig.add_subplot(2,1,1)
        #plt.xlabel('Time (Sec)')
        plt.ylabel('ADC Count')
        #plt.title('Sinusoidal Input (152KHz; Vp-p 1.5V)')
        #plt.title('Sinusoidal Input (17KHz; Vp-p 1.5V)')
        #plt.title('Sinusoidal Input (LN2; 20.5KHz; Vp-p 1.4V;Full Chain; VDDD=2.0V, VDDA=2.5V (Reg0=0x62,Reg4=0x33))')
        #plt.title('Sinusoidal Input (LN2; 20.5KHz; Vp-p 1.4V;SingleEnded SHA-ADC (Reg0=0x63,Reg4=0x3B))')
        #plt.title('Sinusoidal Input (147KHz; Vp-p 1.4V; ADC Only; Nominal CMOS VREF) ')
        #plt.title('Sinusoidal Input (147KHz; Vp-p 1.0V; ADC Only; VREFN/P +/-200mV; Reg23=0x30; Room Temp) ')
        #plt.title('Sinusoidal Input (147KHz; Vp-p 1.5V; ADC Only; Nom CMOS VREF; VDDA2P5=2.5V; Room Temp) ')
        plt.title('Slow Ramp 1.5 Hz; Vin from 200mV to 1.6V ')

        ax1.plot(x0,y0,'.',label='ADC Output')
        ax1.plot(x0,data_fit, label='Fit')
        #ax1.plot(x0,data_first_guess, label='first guess')
        ax1.legend(loc='upper right')
 
        ax2 = fig.add_subplot(2,1,2)
        plt.xlabel('Time (Sec)')
        plt.ylabel('Residuals (16-bit)')
        ax2.plot(x0,residual,'.')
    else:
        ax1 = fig.add_subplot(1,1,1)
        #histTitle="Noise Measurement (ADC Only; VDDA2p5=2.25V; At -70"+chr(176)+"C)"
        histTitle="Noise Measurement (ADC Only; VDDA2p5=2.5V; Room Temperature)"
        #histTitle="Noise Measurement (ADC Only; VDDA2p5=2.25V; LN2 Temperature)"
        plt.title(histTitle)
        plt.ylabel('Counts')
        plt.xlabel('ADC Channel')
        histResults=plt.hist(y0,bins=21, align='mid')
        #histResults=plt.hist(y0,bins=30)
        
        # now do the fit
        mean,std = norm.fit(y0)
        xmin,xmax = plt.xlim()
        #xtmp = np.linspace(xmin,xmax,100)
        xtmp = histResults[1]
        ytmp=norm.pdf(xtmp,mean,std)
        #hRatio=sum(histResults[0])/sum(norm.pdf(histResults[1],mean,std))
        hRatio=sum(histResults[0])/sum(ytmp)
        plt.plot(xtmp,(ytmp*hRatio))
        stdNoise= std * (3.0/2**16) * 10**6

        printMu="Mean = %6.1f "% (mean)
        printWid="Sigma = % 3.2f" % (std)
        printNoise="Noise = %4.1f $\mu$V" % (stdNoise)
        plt.gcf().text(0.65,0.7,printMu)
        plt.gcf().text(0.65,0.65,printWid)
        plt.gcf().text(0.65,0.60,printNoise)
        #plt.text(32685,1500,printWid)
        print("Noise mean, std =", mean, std)

    #Display plot on screen
    plt.show()

    #Save plot to file
    #plt.savefig('temp.png')
    
    # Run FFT
    #fft.AnalyzeDynamicADCTest(y0)
    
    #Exit GPIO cleanly
    GPIO.cleanup

    #Close serial port
    ser.close()

    #Close spi0
    spi0.close()

    #Close output file
    outFile.close()
