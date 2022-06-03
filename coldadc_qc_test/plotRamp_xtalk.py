#!/usr/bin/env python3
 
import time
import binascii
import sys
import RPi.GPIO as GPIO
import spidev
import serial
import readADC
import readCtrlReg
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from scipy.optimize import curve_fit
from scipy.stats import norm
import numpy as np
import fft_test as fft
import csv

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

def plotXtalk2D(csvFile):
    xArray=np.empty((0,16),float)
    with open(csvFile) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            #print(row[1:])
            xArray=np.append(xArray,np.array([row[1:]]),axis=0)
    #print(xArray)
    
    xLabel=["ch0","ch1","ch2","ch3","ch4","ch5","ch6","ch7",
            "ch8","ch9","ch10","ch11","ch12","ch13","ch14","ch15"]
    yLabel=["ch0","ch1","ch2","ch3","ch4","ch5","ch6","ch7",
            "ch8","ch9","ch10","ch11","ch12","ch13","ch14","ch15"]

    fig, ax = plt.subplots()

    '''
    #Differential input (maximum - minimum ADC count)
    yArray=np.array([
        [1.00000, 0.00122, 0.00039, 0.00031, 0.00034, 0.00032, 0.00034, 0.00029, 0.00031, 0.00027, 0.00035, 0.00031, 0.00029, 0.00031, 0.00029, 0.00032],
        [0.00050, 1.00000, 0.00095, 0.00042, 0.00040, 0.00032, 0.00032, 0.00029, 0.00029, 0.00029, 0.00031, 0.00031, 0.00031, 0.00031, 0.00029, 0.00029],
        [0.00032, 0.00047, 1.00000, 0.00093, 0.00039, 0.00037, 0.00032, 0.00031, 0.00031, 0.00031, 0.00031, 0.00029, 0.00029, 0.00031, 0.00031, 0.00032],
        [0.00032, 0.00029, 0.00042, 1.00000, 0.00095, 0.00040, 0.00034, 0.00032, 0.00029, 0.00027, 0.00031, 0.00031, 0.00034, 0.00032, 0.00034, 0.00031],
        [0.00031, 0.00032, 0.00029, 0.00042, 1.00000, 0.00097, 0.00042, 0.00034, 0.00027, 0.00029, 0.00029, 0.00027, 0.00029, 0.00029, 0.00029, 0.00034],
        [0.00035, 0.00031, 0.00031, 0.00032, 0.00037, 1.00000, 0.00097, 0.00039, 0.00032, 0.00031, 0.00032, 0.00034, 0.00034, 0.00035, 0.00034, 0.00031],
        [0.00047, 0.00037, 0.00032, 0.00031, 0.00027, 0.00040, 1.00000, 0.00100, 0.00029, 0.00031, 0.00031, 0.00027, 0.00032, 0.00035, 0.00034, 0.00029],
        [0.00090, 0.00042, 0.00030, 0.00030, 0.00027, 0.00029, 0.00040, 1.00000, 0.00032, 0.00075, 0.00027, 0.00030, 0.00027, 0.00032, 0.00027, 0.00029],
        [0.00032, 0.00029, 0.00030, 0.00030, 0.00027, 0.00034, 0.00032, 0.00030, 1.00000, 0.00078, 0.00034, 0.00032, 0.00027, 0.00029, 0.00030, 0.00029],
        [0.00027, 0.00034, 0.00030, 0.00029, 0.00029, 0.00032, 0.00034, 0.00027, 0.00038, 1.00000, 0.00080, 0.00032, 0.00035, 0.00029, 0.00029, 0.00030],
        [0.00035, 0.00030, 0.00029, 0.00029, 0.00029, 0.00029, 0.00030, 0.00032, 0.00032, 0.00273, 1.00000, 0.00080, 0.00045, 0.00027, 0.00029, 0.00030],
        [0.00030, 0.00037, 0.00032, 0.00030, 0.00027, 0.00030, 0.00030, 0.00034, 0.00032, 0.00027, 0.00046, 1.00000, 0.00088, 0.00042, 0.00035, 0.00032],
        [0.00030, 0.00030, 0.00027, 0.00032, 0.00029, 0.00029, 0.00032, 0.00029, 0.00030, 0.00034, 0.00030, 0.00040, 1.00000, 0.00088, 0.00045, 0.00037],
        [0.00027, 0.00027, 0.00029, 0.00031, 0.00032, 0.00029, 0.00032, 0.00029, 0.00032, 0.00032, 0.00029, 0.00037, 0.00040, 1.00000, 0.00095, 0.00050],
        [0.00029, 0.00032, 0.00027, 0.00029, 0.00032, 0.00032, 0.00031, 0.00034, 0.00037, 0.00032, 0.00035, 0.00031, 0.00035, 0.00040, 1.00000, 0.00100],
        [0.00029, 0.00031, 0.00027, 0.00027, 0.00029, 0.00031, 0.00029, 0.00031, 0.00089, 0.00035, 0.00032, 0.00031, 0.00032, 0.00043, 0.00048, 1.00000]])
    '''

    
    #Single-Ended input (amplitude of sinewave fit)
    yArray=np.array([ 
    [ 1.00000, 0.00075, 0.00005, 0.00004, 0.00005, 0.00006, 0.00006, 0.00001, 0.00004, 0.00003, 0.00002, 0.00002, 0.00002, 0.00002, 0.00001, 0.00001],
        [0.00006, 1.00000, 0.00093, 0.00001, 0.00007, 0.00008, 0.00007, 0.00003, 0.00002, 0.00001, 0.00002, 0.00001, 0.00002, 0.00001, 0.00002, 0.00002],
        [0.00009, 0.00002, 1.00000, 0.00088, 0.00007, 0.00004, 0.00007, 0.00004, 0.00001, 0.00001, 0.00001, 0.00002, 0.00002, 0.00001, 0.00002, 0.00003],
        [0.00020, 0.00004, 0.00011, 1.00000, 0.00096, 0.00013, 0.00004, 0.00002, 0.00002, 0.00002, 0.00002, 0.00002, 0.00002, 0.00002, 0.00002, 0.00003],
        [0.00021, 0.00008, 0.00004, 0.00010, 1.00000, 0.00110, 0.00008, 0.00005, 0.00001, 0.00001, 0.00001, 0.00003, 0.00003, 0.00003, 0.00003, 0.00004],
        [0.00023, 0.00014, 0.00006, 0.00005, 0.00009, 1.00000, 0.00100, 0.00009, 0.00002, 0.00001, 0.00001, 0.00000, 0.00002, 0.00003, 0.00002, 0.00003],
        [0.00028, 0.00017, 0.00007, 0.00004, 0.00007, 0.00014, 1.00000, 0.00109, 0.00001, 0.00001, 0.00001, 0.00001, 0.00003, 0.00004, 0.00003, 0.00001],
        [0.00120, 0.00020, 0.00008, 0.00005, 0.00009, 0.00014, 0.00016, 1.00000, 0.00010, 0.00002, 0.00002, 0.00003, 0.00004, 0.00004, 0.00005, 0.00003],
        [0.00002, 0.00004, 0.00004, 0.00001, 0.00001, 0.00002, 0.00000, 0.00008, 1.00000, 0.00083, 0.00004, 0.00009, 0.00011, 0.00010, 0.00007, 0.00001],
        [0.00002, 0.00003, 0.00003, 0.00001, 0.00001, 0.00001, 0.00002, 0.00002, 0.00002, 1.00000, 0.00064, 0.00006, 0.00012, 0.00012, 0.00009, 0.00003],
        [0.00002, 0.00002, 0.00001, 0.00001, 0.00002, 0.00003, 0.00003, 0.00002, 0.00018, 0.00018, 1.00000, 0.00051, 0.00017, 0.00015, 0.00010, 0.00004],
        [0.00001, 0.00001, 0.00001, 0.00001, 0.00002, 0.00002, 0.00003, 0.00002, 0.00016, 0.00013, 0.00029, 1.00000, 0.00075, 0.00012, 0.00014, 0.00007],
        [0.00001, 0.00001, 0.00001, 0.00002, 0.00002, 0.00001, 0.00002, 0.00002, 0.00016, 0.00015, 0.00019, 0.00011, 1.00000, 0.00105, 0.00015, 0.00018],
        [0.00001, 0.00001, 0.00000, 0.00000, 0.00001, 0.00001, 0.00001, 0.00001, 0.00009, 0.00009, 0.00007, 0.00015, 0.00011, 1.00000, 0.00080, 0.00010],
        [0.00002, 0.00001, 0.00001, 0.00001, 0.00001, 0.00000, 0.00001, 0.00003, 0.00003, 0.00006, 0.00002, 0.00010, 0.00027, 0.00020, 1.00000, 0.00136],
        [0.00004, 0.00002, 0.00002, 0.00001, 0.00001, 0.00001, 0.00002, 0.00003, 0.00111, 0.00005, 0.00002, 0.00003, 0.00025, 0.00036, 0.00028, 1.00000]])
    
    '''
    #Differential input (amplitude of sinewave fit)
    yArray=np.array([ 
        [1.00000, 0.00060, 0.00015, 0.00007, 0.00005, 0.00004, 0.00004, 0.00004, 0.00001, 0.00000, 0.00001, 0.00001, 0.00001, 0.00000, 0.00001, 0.00000],
        [0.00019, 1.00000, 0.00042, 0.00011, 0.00008, 0.00004, 0.00004, 0.00003, 0.00000, 0.00002, 0.00002, 0.00001, 0.00001, 0.00001, 0.00000, 0.00002],
        [0.00006, 0.00017, 1.00000, 0.00064, 0.00015, 0.00010, 0.00006, 0.00005, 0.00000, 0.00000, 0.00001, 0.00000, 0.00001, 0.00000, 0.00001, 0.00000],
        [0.00004, 0.00005, 0.00017, 1.00000, 0.00065, 0.00015, 0.00008, 0.00006, 0.00001, 0.00001, 0.00002, 0.00001, 0.00001, 0.00000, 0.00000, 0.00001],
        [0.00004, 0.00005, 0.00003, 0.00017, 1.00000, 0.00064, 0.00016, 0.00007, 0.00001, 0.00001, 0.00000, 0.00001, 0.00000, 0.00000, 0.00001, 0.00001],
        [0.00007, 0.00005, 0.00005, 0.00003, 0.00011, 1.00000, 0.00060, 0.00013, 0.00001, 0.00001, 0.00001, 0.00002, 0.00001, 0.00001, 0.00001, 0.00001],
        [0.00014, 0.00007, 0.00005, 0.00004, 0.00004, 0.00007, 1.00000, 0.00062, 0.00001, 0.00000, 0.00001, 0.00001, 0.00003, 0.00002, 0.00001, 0.00000],
        [0.00061, 0.00013, 0.00008, 0.00005, 0.00003, 0.00003, 0.00010, 1.00000, 0.00007, 0.00001, 0.00001, 0.00001, 0.00002, 0.00002, 0.00002, 0.00000],
        [0.00001, 0.00001, 0.00001, 0.00002, 0.00001, 0.00001, 0.00002, 0.00004, 1.00000, 0.00053, 0.00008, 0.00002, 0.00001, 0.00000, 0.00001, 0.00002],
        [0.00000, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00000, 0.00001, 0.00014, 1.00000, 0.00051, 0.00007, 0.00001, 0.00001, 0.00002, 0.00003],
        [0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00000, 0.00001, 0.00001, 0.00021, 1.00000, 0.00052, 0.00009, 0.00003, 0.00003, 0.00005],
        [0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00000, 0.00000, 0.00003, 0.00002, 0.00022, 1.00000, 0.00052, 0.00015, 0.00007, 0.00006],
        [0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00000, 0.00005, 0.00001, 0.00003, 0.00017, 1.00000, 0.00056, 0.00018, 0.00012],
        [0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00000, 0.00001, 0.00007, 0.00005, 0.00002, 0.00006, 0.00010, 1.00000, 0.00064, 0.00024],
        [0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00001, 0.00000, 0.00014, 0.00007, 0.00004, 0.00003, 0.00007, 0.00010, 1.00000, 0.00067],
        [0.00001, 0.00001, 0.00001, 0.00002, 0.00002, 0.00001, 0.00002, 0.00001, 0.00061, 0.00013, 0.00007, 0.00003, 0.00006, 0.00014, 0.00013, 1.00000]])
    '''    

    norm=matplotlib.colors.LogNorm() #creates logarithmic scale
    
    #im = ax.imshow(xArray)
    #im = ax.imshow(yArray,cmap='rainbow',norm=norm)
    im = ax.imshow(yArray,cmap='Reds',norm=norm)
    #im = ax.imshow(yArray,cmap='bwr',norm=norm)
    #im = ax.imshow(yArray,cmap='viridis',norm=norm)

    fig.colorbar(im,ax=ax)
    
    ax.set_xticks(np.arange(len(xLabel)))
    ax.set_yticks(np.arange(len(yLabel)))
    #ax.set_xticklabels(xLabel)
    #ax.set_yticklabels(yLabel)

    ax.set_xlabel("ADC Channel #")
    ax.set_ylabel("ADC Channel #")
    
    ## Loop over data dimensions and create text annotations.
    #for i in range(len(xLabel)):
    #    for j in range(len(yLabel)):
    #        text = ax.text(j, i, yArray[i, j],
    #                       ha="center", va="center", color="w")

    
    ax.set_title("ColdADC_P2 Channel Crosstalk")
    fig.tight_layout()
    plt.show()



    
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

# create the fitting function
def my_sin(x, freq, amplitude, phase, offset):
    return np.sin(x * freq + phase) * amplitude + offset



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

    ChSig=15  #Channel with input signal
    ChSigSpan = -1
    xtalk=[]
    ChSigAmp = -1
    xtalkAmp=[]
    
    #Setup plot
    #style.use('fivethirtyeight')
    fig = plt.figure()

    for ich in range (0,16): 
        ChNum = (ADC0Num+ich)%8  # ADC0
        if ich >7 :
            #ChNum = (ADC0Num+ich)%8 + 8  # ADC1
            ChNum += 8
            
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
        
            #y0 += iadcVal
            for jx in range (0,len(iadcVal)):
                x0[ix]=float(ix)*SampRate  
                y0[ix]=iadcVal[jx]
                #iLine=str(x0[ix])+","+str(iadcVal[jx])+"\n"
                iLine=str(iadcVal[jx])+"\n"
                ix += 1
                

        #print("Max, Min ,Diff ADC (16-bit) =",y0.max(), y0.min(), (y0.max()-y0.min()) )         
        adcDiff = (y0.max()-y0.min())
        xtalk.append(adcDiff)

        guess_freq = 110000.0 * (2.0*np.pi)
        guess_amplitude = (y0.max()-y0.min())/2.0
        guess_phase = 0
        guess_offset = np.mean(y0)
        p0=[guess_freq, guess_amplitude, guess_phase, guess_offset]

        # now do the fit
        fit,cov = curve_fit(my_sin, x0, y0, p0=p0)

        # extract the amplitude from the fit
        xtalkAmp.append(2.0*abs(fit[1]))    

        if ChSig == ich :
            ChSigSpan = adcDiff
            ChSigAmp=2.0*abs(fit[1])

            
    #Calculate xtalk
    xtalk[:] = [x / ChSigSpan for x in xtalk]
    xtalkAmp[:] = [x / ChSigAmp for x in xtalkAmp]

    #Write Cross talk results to files
    fOut=open("xtalk.csv","a")
    outLine=str(ChSig)+", "
    for i in xtalk[:-1]:
        outLine+=str("%7.5f"% (i))+", "
    outLine+=str("%7.5f"% xtalk[-1])+"\n"
    print(outLine)
    fOut.write(outLine)

    fOutAmp=open("xtalkAmp.csv","a")
    outLine=str(ChSig)+", "
    for i in xtalkAmp[:-1]:
        outLine+=str("%7.5f"% (i))+", "
    outLine+=str("%7.5f"% xtalkAmp[-1])+"\n"
    print(outLine)
    fOutAmp.write(outLine)

    # Run FFT
    #fft.AnalyzeDynamicADCTest(y0)
    
    #Exit GPIO cleanly
    GPIO.cleanup
    
    #Close serial port
    ser.close()
    
    #Close spi0
    spi0.close()
    
    #Close output file
    fOut.close()
