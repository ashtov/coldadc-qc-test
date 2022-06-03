#!/usr/bin/env python3
#
import time
import serial
import sys
from time import sleep

class SRS_DS360(object):
    """
    Interface to SRS DS360 Function Generator
    """

    def __init__(self):

        self.ser=serial.Serial(
            port='/dev/ttyUSB0',
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.EIGHTBITS,
            timeout=1
            )

    def __del__(self):
        self.ser.close()

    def checkStatus(self):
        time.sleep(0.5)
        self.ser.write('OUTE?\n'.encode())
        time.sleep(0.5)
        status=int(self.ser.readline().decode().strip())
        print (status)
        return status

    def turnON(self):
        self.ser.write('OUTE1\n'.encode())
        time.sleep(0.5)
        self.ser.write('OUTE?\n'.encode())
        time.sleep(0.5)
        x=self.ser.readline().decode()
        print ("Freq On/Off State = ",x)
        return

    def turnOFF(self):
        self.ser.write('OUTE0\n'.encode())
        time.sleep(0.5)
        self.ser.write('OUTE?\n'.encode())
        time.sleep(0.5)
        x=self.ser.readline().decode()
        print ("Freq On/Off State = ",x)
        return

    def setAmpl(self, vpp):
        newVoltage="AMPL"+str(vpp)+"VP\n"
        self.ser.write(newVoltage.encode())
        infoLine="Setting peak-to-peak voltage to "+str(vpp)+" V"
        print(infoLine)
        return

    def setOffset(self, voffset):
        newVoltage="OFFS"+str(voffset)+"\n"
        self.ser.write(newVoltage.encode())
        infoLine="Setting offset voltage to "+str(voffset)+" V"
        print(infoLine)        
        return

    def setFreq(self, freq):
        newFrequency="FREQ"+str(freq)+"\n"
        self.ser.write(newFrequency.encode())
#        infoLine="Setting frequency to "+str(freq)+" Hz"
#        print(infoLine)
        return

    def getAmpl(self):
        readVoltage="AMPL?VP\n"
        self.ser.write(readVoltage.encode())
        vpp = self.ser.readline().decode().strip()
        infoLine="Peak-to-peak voltage is "+str(vpp)+" V"
        print(infoLine)
        return vpp

    def getOffset(self):
        readVOffset="OFFS?\n"
        self.ser.write(readVOffset.encode())
        voffset = self.ser.readline().decode().strip()
        infoLine="Voltage offset is "+str(voffset)+" V"
        print(infoLine)
        return voffset

    def getFreq(self):
        readFrequency="FREQ?\n"
        self.ser.write(readFrequency.encode())
        freq = self.ser.readline().decode().strip()
        infoLine="Frequency is "+str(freq)+" Hz"
        print(infoLine)
        return freq

    def IDN(self):
        self.ser.write('*IDN?\n'.encode())
        idn = self.ser.readline()#.decode().strip()
        print (idn)

    def Reset(self):
        self.ser.write('*RST\n'.encode())


if __name__== '__main__':


    ds360=SRS_DS360()
#    ds360.turnON()
    ds360.turnOFF()
#    ds360.setFreq(47898.438)
    ds360.setFreq(147460)
#    sleep(3)
    ds360.setAmpl(1.44)
    ds360.setOffset(0.9)
    ds360.getFreq()
    ds360.getAmpl()
    ds360.getOffset() 
    status=ds360.checkStatus()
#    ds360.Reset()
#    sleep(10)
#    ds360.checkStatus()


