#!/usr/bin/env python3

import time
import binascii
import sys
import RPi.GPIO as GPIO
import spidev
import serial
import writeCtrlReg
import readCtrlReg
import numpy as np
from random import uniform
from test_equipment.srs_ds360 import SRS_DS360


def deSerialize(iBlock):
    adcOut=[0]*(int((len(iBlock)/2)))

    chNum=0
    iBit=3
    for iWord in iBlock : 
        adcOut[chNum] += ( ((iWord&0x80)>>7<<(iBit)) | ((iWord&0x40)>>6<<(iBit+4)) | 
                         ((iWord&0x20)>>5<<(iBit+8)) |  ((iWord&0x10)>>4<<(iBit+12)) )
        adcOut[chNum+8] += ( ((iWord&0x8)>>3<<(iBit)) | ((iWord&0x4)>>2<<(iBit+4)) | 
                           ((iWord&0x2)>>1<<(iBit+8)) |  ((iWord&0x1)<<(iBit+12)) )
        iBit -= 1
        if iBit < 0 :
            iBit=3
            chNum += 1
            if ( (chNum>7) and (chNum%8 == 0) ):
                chNum += 8
#    print(adcOut)
    return(adcOut)

def pollFIFO(GPort,FIFO_FULL):
    #Poll FPGA Fifo state

    fifoEmpty=True
    #print("Polling FPGA FIFO Status ....")
    while fifoEmpty:
        if GPort.input(FIFO_FULL) == 1 :
            fifoEmpty=False

    #print("FPGA FIFO FULL Detected ...")
    return()

def resetCHIP(GPort, ChipID):

   
    GPort.output(ChipID, GPIO.LOW)
    time.sleep(0.5)
    GPort.output(ChipID, GPIO.HIGH)
    time.sleep(0.5)
    return()

def printADCdata(iData):
    for iCnt in range (0,len(iData)):
        if ((iCnt%16) == 0 ):
            print("------------------------------------------------")
        print("Block",int(iCnt/16)," ADC Ch(",str(iCnt%16).zfill(2),") = ",hex(iData[iCnt]),
              " (",bin(iData[iCnt])[2:].zfill(16),")","(",iData[iCnt],")")
    return()

def printFPGAfifo(iData):
    for iCnt in range (0,len(iData)):
        if ((iCnt%32) == 0 ):
            print("------------------------------------------------")
        print("FPGA Block",int(iCnt/32)," Word(",str(iCnt%32).zfill(2),") = ",hex(iData[iCnt]),
              " (",bin(iData[iCnt])[2:].zfill(16),")")
    return()

def readNSamp(GPort,SPI,FIFO,NWORD,NSamples):

    pollFIFO(GPort,FIFO)
    dummy=SPI.readbytes(NWORD)
    dataSample = []
    t0 = time.time()

    for i in range(0,NSamples):
#        pollFIFO(GPort,FIFO)
#        dummy=SPI.readbytes(NWORD)
#        time.sleep(uniform(100, 500)/1000)

        pollFIFO(GPort,FIFO)

    ##########################################################################
    #Reading out ColdADC FIFO data
    ##########################################################################
#        adcDataBlock=SPI.readbytes(NWORD)
        dataSample.append(SPI.readbytes(NWORD))
    t1 = time.time()

    print("time to read:", t1-t0)
    return dataSample

    
def initSPI():

    spi0 = spidev.SpiDev()
    spi0.open(0,0)
    spi0.max_speed_hz = 8000000
    #spi0.max_speed_hz = 100000
    #mode [CPOL][CPHA]: 0b01=latch on trailing edge of clock
    spi0.mode = 0b01
    return spi0

def initGPIOpoll(fpgaFull):

    GPIO.setmode(GPIO.BCM)
    #GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    #Define GPIO pins
    FPGA_FIFO_FULL=12

    #Set input and output pins
    GPIO.setup(fpgaFull, GPIO.IN)
    return GPIO


if __name__ == '__main__':

    FPGA_FIFO_FULL=12
    UART_SEL=27
    ADC_RESET=6
    FPGA_RESET=22

    NWORDFIFO=65536

    ###ColdADC synchronization. Find ADC channel 0
    ADC0Num=7
    #ADC0Num=findADCch0(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    #print("ADC0 Channel 0 = ",ADC0Num)
    NSamples = 1#int(480*2.5)

    spi = initSPI()
    gport = initGPIOpoll(FPGA_FIFO_FULL)
    rawdata = readNSamp(gport,spi,FPGA_FIFO_FULL,NWORDFIFO,NSamples)

    spi.close()
    gport.cleanup

    for i in range(len(rawdata)):
        firstBlock=rawdata[i][0:NWORDFIFO]

        printFPGAfifo(firstBlock)



