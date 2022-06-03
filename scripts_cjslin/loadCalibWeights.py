#!/usr/bin/env python3

import serial
import time
import binascii
import sys
import re

# Return 0=odd parity, 1=even parity
def parityOf(int_type):
    parity=0
    while (int_type):
        parity = ~parity
        int_type=int_type & (int_type - 1)
    return(parity+1)

# Construct 24-bit UART Word
def uart24bit(word1,word2,word3):
    wordsum = (word1| word2<<8 | word3<<16)&(0x3FFFFF)
    return(wordsum)

# Print memory address info for ADC weights/gain/offset
def printMemoryInfo(pword):
    if (pword&0b01000000):
        print("ADC1 ",end='')
    else:
        print("ADC0 ",end='')
    if (pword&0b00111110) == 30 :
        print("Gain",end='')
    elif ((pword&0b00111110) == 62) :
        print("Offset",end='')
    else:
        print("stage", int((pword&0b11110)>>1), end='')
        if (pword&0b00100000):
            print(", W2",end='')
        else:
            print(", W0",end='')
    if (pword&0b1):
        print (", high byte ", end='')
    else:
        print (", low byte ", end='')


# Defining main()
def main(serial0, regAddress, jdata):
    #Read/Write [0]
    RoW=1          # 0=read; 1=write

    #ChipID [4:1]
    ChipID=0b0110

    #Lower 128 registers
    ConfigFlag=0   # 0=memory registers; 1=config registers

    #Data payload [12:5]
    data1=0
    if (jdata[:2]=="0b"):
        data1=(int(jdata,2))
    elif (jdata[:2]=="0x"):
        data1=(int(jdata,16))
    else:
        data1=int(jdata)
        
    #Construct three UART words
    UWord1=( RoW | ((ChipID&0b1111)<<1) | ((data1&0b111)<<5) )
    UWord2=( ((data1&0b11111000)>>3) | ((regAddress&0b111)<<5) )
    UWord3=( ((regAddress&0b01111000)>>3 | (ConfigFlag&0b1)<<4) )

    UWordSum=uart24bit(UWord1,UWord2,UWord3)

    #Add parity bit
    #print("parity bit = ",parityOf(UWordSum))
    if parityOf(UWordSum):
        #print("Added parity bit to UWordSum and UWord3")
        UWordSum=(UWordSum | 0b1<<21)
        UWord3=(UWord3 | 0b1<<5)

    print("UART 22-bit word : (MSB)",bin(UWordSum)[2:].zfill(22),"(LSB)")
    print("Writing bytes 1,2,3: " ,bin(UWord1)[2:].zfill(8), bin(UWord2)[2:].zfill(8), bin(UWord3)[2:].zfill(8))
    serial0.write(serial.to_bytes([UWord1,UWord2,UWord3]))   
    time.sleep(0.1)
    printMemoryInfo(regAddress)
    print(": wrote to register ", regAddress, " value = " ,bin(data1)[2:].zfill(8), "[",hex(data1),"]", "(", int(data1),")")

    #print("Chip ID = ",int(getChipID(word)))


if __name__ == '__main__':

    if (len(sys.argv) != 2):
        print("\writeCalibWeights.py requires 1 argument: input calibration file name ")
        print("Example:  ./writeCalibWeights.py coldADC_weights_reset2default.txt \n")
        sys.exit()

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
    
    #Input calibration file
    calibFile=open(sys.argv[1],"r")
    calWeights=[]
    for iLine in calibFile:
        if iLine[:3] == "ADC":
            iWeight = iLine.partition("(")[2].partition(")")[0]
            calWeights.append(int(iWeight))

    if (len(calWeights) != 128 ) :
        print("ERROR: file contains only ", len(calWeights), " weights")
        sys.exit()

    idx=0
    #Loop over ADCNum
    for iCnt in range (0,2):
        ADCNum=iCnt
        #Loop over stage address
        for jCnt in range (0,16):
            StageNum=jCnt
            #Loop over W0,W2,gain,offset
            for kCnt in range (0,2):
                CalWeight=kCnt
                #Loop over high/low bite
                for lCnt in range (0,2):
                    ByteNum=lCnt
                    MemAdd=bin(ByteNum | StageNum<<1 | CalWeight <<5 | ADCNum << 6)   
                    idata=str(calWeights[idx])
                    main(ser,int(MemAdd,2),idata)
                    idx +=1

    #print("Chip ID = ",int(getChipID(word)))

    #ser.close()
    calibFile.close()
