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
#    GPIO.output(UART_SEL, GPIO.HIGH)
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

    NumSet=100

    #Options to look at noise in 16, 14, or 12 ADC bits
    adcBit=14
    
    ##############################################
    #Readout Mode (0=read ADC0 block, 1=read ADC1 block, 2=single channel read)
    #             ChNum ignored if ReadMode!=2
    #NoiseStudy = 0  (0=data mode; 1= noise study)
    ##############################################
    ReadMode=2
    NoiseStudy = 1

    #Setup plot
    #style.use('fivethirtyeight')
    fig = plt.figure()

    avgNoise=[]

    #Warm differential inputs 1.4V span (P2 ASIC#1)
    #ADCSpan1p4V=np.array([59951., 59593, 60893., 60933., 60936., 60946.,
    #                      60965., 60978., 59953.,60940., 60921., 60992.,
    #                      61004., 60957., 60988., 61029.])

    #LN2 differential inputs 1.4V span  (P2 ASIC#1)
    #ADCSpan1p4V=np.array([60654., 60665., 60605., 60660., 60599., 60532.,
    #                      60624., 60628., 60724., 61312., 60735., 60757.,
    #                      60744., 60620., 60655., 60760.])
     
    #LN2 single-ended inputs (P2 ASIC#1)
    #ADCSpan1p4V=np.array([56206., 56320., 56280., 56322., 56243., 56215.,
    #                      56320., 56315., 56301., 59262., 56360., 65436.,
    #                      56444., 56397., 56437., 56452.])

    
    #LN2 differential inputs 1.4V span  (P2 ASIC#2)
    #ADCSpan1p4V=np.array([60705., 60765., 60481., 60352., 60658., 60591.,
    #                      60734., 60743., 60830., 60876., 60834., 60856.,
    #                      60842., 60757., 60784., 60852.])

    #LN2 differential inputs (P2 packaged serial#0044)
    #ADCSpan1p4V=np.array([61792., 61840., 61760., 61792., 61808., 61792.,
    #                      61824., 61872., 61536., 61520., 61379., 61312.,
    #                      61200., 61152., 61168., 61136.])

    #LN2 Single Ended ColdADC_P1 (bare die #2)
    ADCSpan1p4V=np.array([61664., 60816., 60784., 60912., 60928., 60944.,
                          60928., 60896., 60976., 60960., 60880., 61024.,
                          61008., 60992., 60992., 61120.])
    
    #Conversion factor for differential input
    #volt2adc=(1.4*2.0*(10**6))/(ADCSpan1p4V)

    #Conversion factor for single-ended input
    volt2adc=(1.4*1.0*(10**6))/(ADCSpan1p4V)

    #for ich in range (8,16):   #ADC1
    for ich in range (0,8):   #ADC0

        ChNum = (ADC0Num+ich)%8  # ADC0
        #ChNum = (ADC0Num+ich)%8 + 8  # ADC1

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

            #print("Length of iadcVal = ",len(iadcVal))

            if adcBit == 14:
                iadcVal = [icode/4.0 for icode in iadcVal]
            if adcBit == 12:
                iadcVal = [icode/16.0 for icode in iadcVal]
            
            #y0 += iadcVal
            for jx in range (0,len(iadcVal)):
                x0[ix]=float(ix)*SampRate  
                y0[ix]=iadcVal[jx]
                #iLine=str(x0[ix])+","+str(iadcVal[jx])+"\n"
                iLine=str(iadcVal[jx])+"\n"
                outFile.write(iLine)
                ix += 1

        fig.add_subplot(2,4,(ich+1))
        #fig.add_subplot(2,4,(ich-7))

        #histTitle="Noise Measurement (ADC Only; VDDA2p5=2.25V; At -70"+chr(176)+"C)"
        histTitle="CH"+str(ich)
        plt.title(histTitle,fontsize=10)
        plt.ylabel('Counts',fontsize=8)
        if (ich<4 or (ich>7 and ich<12)) :
            plt.xlabel('',fontsize=8)
        else:
            plt.xlabel('ADC Code (16bit)',fontsize=8)
            if adcBit == 14:
                plt.xlabel('ADC Code (14bit)',fontsize=8)
            if adcBit == 12:
                plt.xlabel('ADC Code (12bit)',fontsize=8)
            
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=8)
        histResults=plt.hist(y0,bins=15, align='mid')
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

        factor=1.0
        if adcBit == 14:
            factor = 4.0
        if adcBit == 12:
            factor = 16.0
        
        stdNoise= std * factor * volt2adc[ich]
       
        printMu="Mean = %6.1f "% (mean)
        printWid="Sigma = % 3.2f" % (std)
        printNoise="Noise = %4.1f $\mu$V" % (stdNoise)
        #plt.gcf().text(0.65,0.7,printMu)
        #plt.gcf().text(0.65,0.65,printWid)
        #plt.gcf().text(0.65,0.60,printNoise)
        ##plt.text(32685,1500,printWid)
        print("Noise mean, std(adc cnt), std(uV) = %5.2f, %5.2F, %5.2F" %( mean, std, stdNoise))
        avgNoise.append(stdNoise)

    print("Average ADC Noise (uV)= ",np.mean(avgNoise))
    plt.tight_layout()     
    plt.show()

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
