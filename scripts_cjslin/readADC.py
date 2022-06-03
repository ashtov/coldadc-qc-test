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

def testWord():
    testPat=[0b1000,0,0,0,0b1000,0,0,0b10001000,0b1000,0,0b10001000,0,
             0b1000,0,0b10001000,0b10001000,0b1000,0b10001000,0,0,0b1000,
             0b10001000,0,0b10001000,0b1000,0b10001000,0b10001000,0,0b1000,
             0b10001000,0b10001000,0b10001000]
    return testPat

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

def findADCch0(gport,spi,serial0,fifo,nword):

    #Check cofig register 50
    Reg50Val=readCtrlReg.main(serial0,50)
    if (Reg50Val != 0 ) :
        print("ERROR!!!!  Config register#50 is non-zero, set all bits to zero for ADC sync")
        sys.exit()
                
    Reg9Val=readCtrlReg.main(serial0,9)

    #Configure coldADC to sync mode and output in 2's complement
    writeCtrlReg.main(serial0,9,str(0b11000))

    ################
    #Read FPGA RAM
    ################
    

    ##########################################################################
    #Poll FPGA FIFO state and read FPGA FIFO words
    #Due to FPGA timing issue, first two words in the FPGA RAM are discarded
    ##########################################################################
    pollFIFO(gport,fifo)
    iDataBlock=spi.readbytes(nword)
    pollFIFO(gport,fifo)
    iDataBlock=spi.readbytes(nword)
    pollFIFO(gport,fifo)
    iDataBlock=spi.readbytes(nword)

    iBlock=iDataBlock[0:32]

    iData = deSerialize(iBlock)[0:8]
    #printADCdata(iData)

    #Now find peak channel
    chMaxVal=max(iData[0:8])
    chMax=np.argmax(iData[0:8])
    chMinVal=min(iData[0:8])
    chMin=np.argmin(iData[0:8])

    #Check that chMax+1 is mid-scale, chMax+2 is low scale 
    if ( chMin != (chMax+2)%8 ):
        print(" ============================================")
        print("Error, ADC_Ch_Min is not (ADC_Ch_Max + 2) ...")
        print(" ============================================")
        sys.exit()

    #Configure ColdADC to normal operation
    if (Reg9Val != 0 ) :
        print("ADC sync completed, restoring register#9 to ",Reg9Val)
        writeCtrlReg.main(serial0,9,str(Reg9Val))
    else:
        writeCtrlReg.main(serial0,9,str(0))
        
    return(chMax)

def fpgaFifoOK(fifoData):
    itempD=0
    dupCnt=0
    ErrCut=int(len(fifoData)*0.65)
    for iCnt in range (0,len(fifoData)):
        if itempD == fifoData[iCnt]:
            dupCnt += 1
        if dupCnt > ErrCut :
            #print("Corrupted FPGA FIFO flagged ..... ")
            return(dupCnt)
        itempD=fifoData[iCnt]
    return(dupCnt)

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

def checkADCdata(iData):
    for iCnt in range (0,len(iData)):
        if iCnt%16<8 and iData[iCnt] != 0xabcd:
            print("failed")
            return False
        if iCnt%16>=8 and iData[iCnt] != 0x1234:
            print("failed")
            return False
    print("success")

def printFPGAfifo(iData):
    for iCnt in range (0,len(iData)):
        if ((iCnt%32) == 0 ):
            print("------------------------------------------------")
        print("FPGA Block",int(iCnt/32)," Word(",str(iCnt%32).zfill(2),") = ",hex(iData[iCnt]),
              " (",bin(iData[iCnt])[2:].zfill(16),")")
    return()


# Defining main()
def main(GPort,SPI,SERIAL0,FIFO,NWORD):
    #testPattern=testWord()
    #print("Number of words = ",len(testPattern))

    #adcData = deSerialize(testPattern)
    #print(testPattern)
    #print(adcData)

    #Poll FPGA FIFO state
    t0 = time.time()
    pollFIFO(GPort,FIFO)

    ##########################################################################
    #Reading out ColdADC FIFO data
    ##########################################################################
    adcDataBlock=SPI.readbytes(NWORD)
    t1 = time.time()

    firstBlock=adcDataBlock[0:NWORD]
    #printFPGAfifo(firstBlock)

    #Deserialize ADC data
    deSerData = deSerialize(firstBlock)      
    t2 = time.time()
    #print("time to read:", t1-t0)
    #print("time to process:", t2-t1)

    return(deSerData)


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
    #spi0.max_speed_hz = 100000
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

    #resetCHIP(GPIO, FPGA_RESET)
    #resetCHIP(GPIO, ADC_RESET)

    #Number of words in FPGA FIFO
    #NWORDFIFO=4096
    NWORDFIFO=65536

    ###ColdADC synchronization. Find ADC channel 0
    ADC0Num=7
    #ADC0Num=findADCch0(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    #print("ADC0 Channel 0 = ",ADC0Num)


    deSerialData=main(GPIO,spi0,ser,FPGA_FIFO_FULL,NWORDFIFO)
    printADCdata(deSerialData)

    #Exit GPIO cleanly
    GPIO.cleanup

    #Close serial port
    ser.close()

    #Close spi0
    spi0.close()

