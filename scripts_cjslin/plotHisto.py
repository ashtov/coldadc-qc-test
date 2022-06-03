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


def getADCVal(ADC_Data,chnum):
    adcArray=[]
    ichnum=chnum
    for iCnt in range (0,int((len(ADC_Data))/16)):
        adcArray.append(ADC_Data[ichnum])
        ichnum += 16
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
    spi0.max_speed_hz = 1000000
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

    outFile = [None]*16
    ###Open output files (1 per channel)
    for ix in range (0,16):
    #for ix in range (0,1):
        fileName="FE-DiffSHA-ADC_Noise_VDDD1P2_2V_diffBufBypass_Ch"+str(ix)+".txt"
        #fileName="FE-DiffSHA-ADC_Noise_VDDD1P2_2V_SDCBypass_Ch"+str(ix)+".txt"
        #fileName="FE-SHA-ADC_Noise_VDDD1P2_2V_SDCBypass_Ch"+str(ix)+".txt"
        #fileName="SingleEndedSHA-ADC_Noise_VDDD1P2_2V_Ch"+str(ix)+".txt"
        #fileName="DifferentialSHA-ADC_Noise_VDDD1P2_2V_Ch"+str(ix)+".txt"
        #fileName="ADC_Noise_VDDA_2p5_NomREf_Open_Ch"+str(ix)+".txt"
        #fileName="test_Ch"+str(ix)+".txt"
        outFile[ix]=open(fileName,"w")

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

    #Number of reads per set
    NumSet=10

    ##############################################
    # Plot ADC Output for one channel
    ##############################################
    ChNum = 2

    #Setup plot
    #style.use('fivethirtyeight')
    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1)
    plt.xlabel('ADC Channel Number')
    plt.ylabel('Counts')
    plt.title('ADC Code for Sine Wave (12-bit)')

    y0 = []

    ix = [0 for n in range(16)]
    #ix = [0 for n in range(1)]
    idummy=readADC.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    for iLoop in range(0,NumSet):
        deSerialData=readADC.main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
        for iCh in range(0,16) :
        #for iCh in range(0,1) :
            iadcVal = getADCVal(deSerialData,iCh)
            #### Divide ADC value by 16 for 12-bit 
            #y0 += [x/16.0 for x in iadcVal]
            for jx in range (0,len(iadcVal)):
                ix[iCh] += 1
                #iLine=str(ix[iCh])+","+str(iadcVal[jx])+"\n"
                iLine=str(iadcVal[jx])+"\n"
                outFile[iCh].write(iLine)
            
    #plt.hist(y0,bins=4096, align='mid')
    #plt.show()

    #Exit GPIO cleanly
    GPIO.cleanup

    #Close serial port
    ser.close()

    #Close spi0
    spi0.close()

    ###Close output file
    for ix in range (0,16):
    #for ix in range (0,1):
        outFile[ix].close()

