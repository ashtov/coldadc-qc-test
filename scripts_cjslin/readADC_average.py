#!/usr/bin/env python3

import time
import binascii
import sys
import RPi.GPIO as GPIO
import spidev
import serial
import readADC
import writeCtrlReg
import readCtrlReg
import writeCalibWts

def calcAvg(ADC_Data):
    ADCSum=[0,0]
    NumEvt=len(ADC_Data)
    jCnt=0
    ADC1=0
    ADC2=0
    for iCnt in range(0,NumEvt):
        if jCnt < 8 :
            ADCSum[0] += ADC_Data[iCnt]
            jCnt += 1
            ADC1 += 1
        else:
            ADCSum[1] += ADC_Data[iCnt]
            jCnt += 1
            ADC2 += 1
        if jCnt == 16:
            jCnt=0
    avgADC=[i*(2.0/NumEvt) for i in ADCSum]
    return(avgADC)


def computeAvgADC(GPort,SPI0,SERIAL0,FIFO_FULL,NWORD,numset):
    AvgADC=[0,0]
    NumDataEvt=0
    idummy=readADC.main(GPort,SPI0,SERIAL0,FIFO_FULL,NWORD)
    idummy=readADC.main(GPort,SPI0,SERIAL0,FIFO_FULL,NWORD)
    deSerialData1=readADC.main(GPort,SPI0,SERIAL0,FIFO_FULL,NWORD)
    for iLoop in range(0,numset):
        deSerialData2=readADC.main(GPort,SPI0,SERIAL0,FIFO_FULL,NWORD)
        #printADCdata(deSerialData2)

        if (deSerialData2[0] == 0) :
            deSerialData1=readADC.main(GPort,SPI0,SERIAL0,FIFO_FULL,NWORD)
            continue

        iAvgADC = calcAvg(deSerialData1)
        AvgADC[0] += iAvgADC[0]
        AvgADC[1] += iAvgADC[1]
        deSerialData1 = deSerialData2

        NumDataEvt += 1

    AvgADC=[i*(1./NumDataEvt) for i in AvgADC]
    return(AvgADC)

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
    spi0.max_speed_hz = 753000
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
    NWORDFIFO=1024

    #ColdADC synchronization. Find ADC channel 0
    ADC0Num=3
    #ADC0Num=readADC.findADCch0(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    #print("ADC0 Channel 0 = ",ADC0Num)

    #Number of reads per set
    NumSet=100

    #Verify both registers 9 and 50 are set to 0
    #checkRegisters(ser)

    ##############################################
    # Calculate Average ADC
    ##############################################
    adcAvg=computeAvgADC(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO,NumSet)
    print(adcAvg)

    
    #Exit GPIO cleanly
    GPIO.cleanup

    #Close serial port
    ser.close()

    #Close spi0
    spi0.close()

