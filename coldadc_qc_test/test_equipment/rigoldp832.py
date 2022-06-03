#!/usr/bin/env python3
#
# This example show how to use PyVisa to read the status of
# Rigol DP832 power supply
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import open
from future import standard_library

import sys
import pyvisa as visa
import time
import argparse

standard_library.install_aliases()
import os


class RigolDP832(object):

    def __init__(self):
        self.powerSupplyDevice = None
#        PSModel="Rigol DP832"
        #Address of Rigol Power Supply
#        PSAddress="USB0::0x1AB1::0x0E11::DP8C185151539::0::INSTR"
        PSModel="Keithley 2230-30"
        PSAddress="USB0::1510::8752::9204362::0::INSTR"


        rm = visa.ResourceManager()
        #print(rm.list_resources())
        self.powerSupplyDevice = rm.open_resource(PSAddress)
#        self.off(1)
#        self.off(3)
#        self.set_channel(2, 5.0, None, None, float(0.5))
#        self.on(2)
        self.powerSupplyDevice.write("OUTP:ENAB ON")

    def on(self, channels = [1,2,3]):
        if type(channels) is not list:
            if ((int(channels) < 1) or (int(channels) > 3)):
                print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channels))
                return
            self.powerSupplyDevice.write("INST:NSEL {}".format(channels))
#            self.powerSupplyDevice.write("VOLT 2.4")                    
            self.powerSupplyDevice.write("CHAN:OUTP ON")
            if (self.get_on_off(channels) != True):
                print("RigolDP832 Error --> Tried to turn on Channel {} of the Rigol DP832, but it didn't turn on".format(channels))
        else:
            for i in channels:
                if ((int(i) < 1) or (int(i) > 3)):
                    print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(i))
                    return

            for i in channels:
                self.powerSupplyDevice.write("INST:NSEL {}".format(i))
                self.powerSupplyDevice.write("CHAN:OUTP ON")
                if (self.get_on_off(i) != True):
                    print("RigolDP832 Error --> Tried to turn on Channel {} of the Rigol DP832, but it didn't turn on".format(i))

        return True
    

    def off(self, channels = [1,2,3]):
        if type(channels) is not list:
            if ((int(channels) < 1) or (int(channels) > 3)):
                print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channels))
                return
            self.powerSupplyDevice.write("INST:NSEL {}".format(channels))
#            self.powerSupplyDevice.write("VOLT 0")
            self.powerSupplyDevice.write("CHAN:OUTP OFF")
            if (self.get_on_off(channels) != False):
                print("RigolDP832 Error --> Tried to turn off Channel {} of the Rigol DP832, but it didn't turn off".format(channels))
        else:
            for i in channels:
                if ((int(i) < 1) or (int(i) > 3)):
                    print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(i))
                    return

            for i in channels:
                self.powerSupplyDevice.write("INST:NSEL {}".format(i))
                self.powerSupplyDevice.write("CHAN:OUTP OFF")                
                if (self.get_on_off(i) != False):
                    print("RigolDP832 Error --> Tried to turn off Channel {} of the Rigol DP832, but it didn't turn off".format(i))

    
    def get_on_off(self, channel):
        self.powerSupplyDevice.write("INST:NSEL {}".format(channel))
        resp = self.powerSupplyDevice.query("CHAN:OUTP?")
        resp = resp.strip()
        status = None
        if (resp == "1"):
            status = True
        elif (resp == "0"):
            status = False
        return (status)

    def measure_power(self,channel):
        if ((int(channel) < 1) or (int(channel) > 3)):
            print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channel))
            return

        response = self.powerSupplyDevice.query(":MEAS:POW? CH{}".format(channel))
        response = response.strip()
        return response

    def measure_voltage(self,channel):
        if ((int(channel) < 1) or (int(channel) > 3)):
            print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channel))
            return

        response = self.powerSupplyDevice.query(":MEAS:VOLT? CH{}".format(channel))
        response = response.strip()
        return response

    def measure_current(self,channel):
        if ((int(channel) < 1) or (int(channel) > 3)):
            print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channel))
            return

        response = self.powerSupplyDevice.query(":MEAS:CURR? CH{}".format(channel))
        response = response.strip()
        return response

    #Set all useful parameters of a channel.  Will ignore setting parameters that were not explicitly passed as arguments.
    def set_channel(self, channel, voltage = None, current = None, v_limit = None, c_limit = None, vp = None, cp = None):
        if (voltage and current):
            print("RigolDP832 Error --> Can't set both voltage and current for Channel {}".format(channel))

        self.powerSupplyDevice.write("INST:NSEL {}".format(channel))

        if (voltage):
            if ((voltage > 0) and (voltage < 30)):
                self.powerSupplyDevice.write("VOLT {}".format(voltage))
                response = float(self.powerSupplyDevice.query("VOLT?"))
                print(response)
                if (response != voltage):
                    print("RigolDP832 Error --> Voltage was set to {}, but response is {}".format(voltage, response))
            else:
                print("RigolDP832 Error --> Voltage must be between 0 and 30 Volts, was {}".format(voltage))

        if (current):
            if ((current > 0) and (current < 3)):
                self.powerSupplyDevice.write("CURR {}".format(current))
                response = float(self.powerSupplyDevice.query("CURR?"))
                if (response != current):
                    print("RigolDP832 Error --> Current was set to {}, but response is {}".format(current, response))
            else:
                print("RigolDP832 Error --> Current must be between 0 and 3 Amps, was {}".format(current))

        if (v_limit):
            if ((v_limit > 0.01) and (v_limit < 33)):
                self.powerSupplyDevice.write("VOLT:LIM {}".format(v_limit))
                response = float(self.powerSupplyDevice.query("VOLT:LIM?").strip())
                if (response != v_limit):
                    print("RigolDP832 Error --> Voltage protection was set to {}, but response is {}".format(v_limit, response))
            else:
                print("RigolDP832 Error --> OverVoltage protection must be between 0.01 and 30 Volts, was {}".format(v_limit))

        if (c_limit):
            if ((c_limit > 0.001) and (c_limit < 3.3)):
                self.powerSupplyDevice.write("CURR:LIM {}".format(c_limit))
#                response = float(self.powerSupplyDevice.query("CURR:LIM?").strip())
#                if (response != c_limit):
#                    print("RigolDP832 Error --> Current protection was set to {}, but response is {}".format(c_limit, response))
            else:
                print("RigolDP832 Error --> OverCurrent protection must be between 0.001 and 3.3 Amps, was {}".format(c_limit))

        if (vp):
            if ((vp == "ON") or (vp == "OFF")):
                self.powerSupplyDevice.write("VOLT:LIM:STAT {}".format(vp))
                response = float(self.powerSupplyDevice.query(":VOLT:LIM:STAT?").strip())
                if ((vp == "ON" and response != 1) or (vp == "OFF" and response != 0)):
                    print("RigolDP832 Error --> OverVoltage was set to {}, but response is {}".format(vp, response))
            else:
                print("RigolDP832 Error --> OverVoltage protection must be 'ON' or 'OFF', was {}".format(vp))

        if (cp):
            if ((cp == "ON") or (cp == "OFF")):
                self.powerSupplyDevice.write("CURR:LIM:STAT {}".format(cp))
                self.powerSupplyDevice.write("CURR:LIM:STAT?")
#                response = float(self.powerSupplyDevice.query("CURR:LIM:STAT?").strip())
#                if ((cp == "ON" and response != 1) or (cp == "OFF" and response != 0)):
#                    print("RigolDP832 Error --> OverCurrent was set to {}, but response is {}".format(cp, response))
            else:
                print("RigolDP832 Error --> OverCurrent protection must be 'ON' or 'OFF', was {}".format(cp))

    
    
    def beep(self):
        self.powerSupplyDevice.write(":SYSTem:BEEPer:IMMediate")
        return True

    
if __name__== '__main__':
   
#    channel = int(sys.argv[1]) 

    rigolPS=RigolDP832()   
#    rigolPS.off(3)
#    rigolPS.set_channel(2, current = 0.01, cp = "ON")
#    rigolPS.set_channel(2, current = 0.01)
#    rigolPS.set_channel(2, voltage = 2.0, v_limit = 2.5, vp = "ON")
#    rigolPS.powerSupplyDevice.write("OUTP:ENAB ON")
#    for i in range(1,4):
#        rigolPS.off(i)
#        rigolPS.on(i)
#        print(rigolPS.get_on_off(i))
    
    
        
