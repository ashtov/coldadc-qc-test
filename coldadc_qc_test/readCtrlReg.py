#!/usr/bin/env python3

import serial
import time
import binascii
import sys

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

# Extract data payload from UART word
def getData(uword):
    dataPayload=( ((uword[0]&0b11100000)>>5) | ((uword[1]&0b00011111)<<3) )
    return(dataPayload)

# Extract memory address from UART word
def getAddress(uword):
    dataAddress=( ((uword[1]&0b11100000)>>5) | ((uword[2]&0b00011111)<<3) )
    return(dataAddress)


# Defining main()
def readReg(regAddress):

    serial0 = serial.Serial(
        port='/dev/serial0',
        baudrate=1000000,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS)

    print (serial0.portstr)

    #Clear Serial buffers
    serial0.flush()
    #ser.flushInput()
    #ser.flushOutput()



    #Read/Write [0]
    RoW=0          # 0=read; 1=write

    #ChipID [4:1]
    ChipID=0b0110

    #Upper 128 registers
    ConfigFlag=1   # 0=memory registers; 1=config registers

    #Data payload [12:5]
    data1=0
        
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

    #print("UART 22-bit word : (MSB)",bin(UWordSum)[2:].zfill(22),"(LSB)")
    #print("Writing bytes 1,2,3: " ,bin(UWord1)[2:].zfill(8), bin(UWord2)[2:].zfill(8), bin(UWord3)[2:].zfill(8))
    serial0.write(serial.to_bytes([UWord1,UWord2,UWord3]))   
    time.sleep(0.1)
    

    #Reading three bytes from Raspberry Pi serial buffer
    word=[0]*3
    for iCnt in range (0,3):
        word[iCnt]=int(binascii.hexlify(serial0.read(1)),16)
    dataWord=getData(word)
    serial0.close()
    return(dataWord)


if __name__ == '__main__':

    if (len(sys.argv) != 2):
        print("\readCtrlReg.py requires 1 argument: address (int) ")
        print("Example:  ./readCtrlReg.py 31 \n")
        sys.exit()
    
    #Set register address (config bit is already set to 1)
    iAddress=int(sys.argv[1])

    regVal=readReg(iAddress)
    print("Reading config register",iAddress, " value = ", regVal, "(",bin(regVal),")" , "(",hex(regVal),")");
    
    #print("Chip ID = ",int(getChipID(word)))

