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
    #wordsum = (word1| word2<<8 | word3<<16)&(0x3FFFFF)
    wordsum = (word1| word2<<8 | word3<<16)
    return(wordsum)

# Defining main()
def writeReg_i2c(regPage, regAddress, jdata):

    serial0 = serial.Serial(
        port='/dev/serial0',
        baudrate=1000000,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS)

#    print (serial0.portstr)

    #Clear Serial buffers
    serial0.flush()
    #ser.flushInput()
    #ser.flushOutput()

    #Read/Write [0]
    RoW=0          # 1=read; 0=write
    #registerPageAddress
    regPageAddress=0b001

    if(regPage==1):
        regPageAddress=0b001
    elif(regPage==2):
        regPageAddress=0b010

    print(regPageAddress)

    #ChipID [4:1]
    ChipID=0b0110

    #Upper 128 registers
    ConfigFlag=1   # 0=memory registers; 1=config registers

    #Data payload [12:5]
    data1=0
    if (jdata[:2]=="0b"):
        data1=(int(jdata,2))
    elif (jdata[:2]=="0x"):
        data1=(int(jdata,16))
    else:
        data1=int(jdata)
        
    #Construct three UART words
    UWord1=( RoW | ((regPageAddress&0b111)<<1) | ((ChipID&0b1111)<<4) )
    #UWord2=( ((data1&0b11111000)>>3) | ((regAddress&0b111)<<5) )
   # UWord3=( ((regAddress&0b01111000)>>3 | (ConfigFlag&0b1)<<4) )
    UWord2=( regAddress&0b11111111) 
    UWord3=( data1&0b11111111 )

    UWordSum=uart24bit(UWord1,UWord2,UWord3)

    #Add parity bit
    #print("parity bit = ",parityOf(UWordSum))
#    if parityOf(UWordSum):
#        #print("Added parity bit to UWordSum and UWord3")
#        UWordSum=(UWordSum | 0b1<<21)
#        UWord3=(UWord3 | 0b1<<5)

    #print("UART 22-bit word : (MSB)",bin(UWordSum)[2:].zfill(22),"(LSB)")
    #print("Writing bytes 1,2,3: " ,bin(UWord1)[2:].zfill(8), bin(UWord2)[2:].zfill(8), bin(UWord3)[2:].zfill(8))
    serial0.write(serial.to_bytes([UWord1,UWord2,UWord3]))   
    time.sleep(0.1)
    print("Wrote to config register ", regAddress, " value = " ,bin(data1)[2:].zfill(8), "[",hex(data1),"]", "(", int(data1),")")

    #print("Chip ID = ",int(getChipID(word)))
    serial0.close()

if __name__ == '__main__':

    if (len(sys.argv) != 4):
        print("\writeCtrlReg.py requires 3 arguments: page(1 or 2) address (int) and value (int,0x,0b)")
        print("Example:  ./writeCtrlReg.py 1 31 0b100 \n")
        sys.exit()

    iPage=int(sys.argv[1])
    if (iPage !=1 and iPage != 2):
        print("Incorrect register page number. (Only 1 or 2) \n")
        sys.exit()

    iAddress=int(sys.argv[2])
    idata=sys.argv[3]
    

    writeReg_i2c(iPage,iAddress,idata)
    
    #print("Chip ID = ",int(getChipID(word)))

