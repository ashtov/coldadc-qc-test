#!/usr/bin/env python3

import os,sys
import serial
import time
import binascii

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

# Extract memory address from UART word
def getChipID(wword):
    cID=( (wword[0]&0b11110)>>1 )
    return(cID)

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
                

ser = serial.Serial(
    port='/dev/serial0',
    baudrate=1000000,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)

print (ser.portstr)

#Open output file to read memory address and payload
fInput=open('Memory_Data.txt','r') 

#Read/Write [0]
RoW=0          # 0=read; 1=write

#Initialize values 
#ChipID [4:1]
ChipID=0b0110

#Data payload [12:5]
data1=0

#Configuration memory [20:13]
ADCNum=0       # 0=ADC0; 1=ADC1
CalWeight=0    # 0=W0; 1=W2
StageNum=0    # Pipeline stage number from 0-15
ByteNum=0      # 0=lower signifcant byte; 1=higher significant byte
ConfigFlag=0   # 0=memory registers; 1=config registers
MemAdd=bin(ByteNum | StageNum<<1 | CalWeight <<5 | ADCNum << 6)


#Clear Serial buffers
ser.flush()
#ser.flushInput()
#ser.flushOutput()

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

                #Construct three UART words
                UWord1=( RoW | ((ChipID&0b1111)<<1) | ((data1&0b111)<<5) )
                UWord2=( ((data1&0b11111000)>>3) | (ByteNum<<5) | ((StageNum&0b11)<<6))
                UWord3=( ((StageNum&0b1100)>>2) | (CalWeight<<2) | (ADCNum<<3) | (ConfigFlag&0b1)<<4)

                UWordSum=uart24bit(UWord1,UWord2,UWord3)

                #Add parity bit
                if parityOf(UWordSum):
                    #print("Added parity bit to UWordSum and UWord3")
                    UWordSum=(UWordSum | 0b1<<21)
                    UWord3=(UWord3 | 0b1<<5)

                #print("=================================================================")
                #print("UART 22-bit word : (MSB)",bin(UWordSum)[2:].zfill(22),"(LSB)")

                #print("Writing bytes 1,2,3: " ,bin(UWord1)[2:].zfill(8), bin(UWord2)[2:].zfill(8), bin(UWord3)[2:].zfill(8))
                ser.write(serial.to_bytes([UWord1,UWord2,UWord3]))   

                time.sleep(0.05)

                #Reading three bytes from Raspberry Pi serial buffer
                word=[0]*3
                #print("\nReading bytes 1,2,3 : ",end='')
                for iCnt in range (0,3):
                    word[iCnt]=int(binascii.hexlify(ser.read(1)),16)
                #print(bin(word[0])[2:].zfill(8),bin(word[1])[2:].zfill(8),bin(word[2])[2:].zfill(8))

                addWord=getAddress(word)
                #print("Memory address = ",bin(addWord)[2:].zfill(8), "[",hex(addWord),"]", "(", int(addWord),")")
                printMemoryInfo(addWord)
                dataWord=getData(word)
                print(" data = ",bin(dataWord)[2:].zfill(8), "[",hex(dataWord),"]", "(", int(dataWord),")",end='')

                #print("Chip ID = ",int(getChipID(word)))
                print(" ")

                # Read payload
#                iData=int(fInput.readline())
#                if (dataWord != iData) :
#                    print(" Error: diff=",bin(iData^dataWord)[2:].zfill(8))
#                else:
#                    print(": Error=0")


fInput.close()
ser.close()

