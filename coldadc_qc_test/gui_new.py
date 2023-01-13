#!/usr/bin/python3

# gui_new.py new version, mostly same as old ('gui_new.py' of 2022-04-14), but
# linearity calculation now runs in 1.3 seconds rather than 38 minutes.
# 
# Use with same date qc_dnl_inl_newer.py and deserialize.c
# 
# It also now sensibly calls run_linearity() from run_qc(), rather than
# duplicating all the code like it used to (this previously led to different
# behaviour between clicking linearity test button and running a full qc test
# due to code modifications in the latter not mirrored in the former).
# 
# modifications ashtov 2022-06-01, original author ???

"""
ADC Test Stand GUI
"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import int
from builtins import str
from builtins import hex
from future import standard_library
standard_library.install_aliases()
import datetime
import socket
import os
import os.path
import pwd
import sys
import glob
import json
#import pprint
from time import sleep
from time import time   # DEBUG
from tkinter import *
from tkinter import ttk
from tkinter import messagebox 
import subprocess
import argparse

import numpy as np

from test_equipment.srs_ds360 import SRS_DS360
from test_equipment.rigoldp832 import RigolDP832
from readCtrlReg import readReg
from readCtrlReg_i2c import readReg_i2c
from readVReff import readVolts
from writeCtrlReg_i2c import writeReg_i2c
from readCalibWeights import readCalib
# import readADC_NSamp_new
import qc_dnl_inl_newer

#import the test module
#import femb_python
#from ...configuration import CONFIG
#from ...runpolicy import DirectRunner, SumatraRunner

GUITESTMODE=False

MYTIME = 0


class GUI_WINDOW(Frame):


####### Initial values ##### Could move into a input config file
    ps_interface = None
    ps_interface = RigolDP832()
    srs_interface = None
    srs_interface = SRS_DS360()
    vinit_regs    = [24, 25, 26, 27]
    #sinit_regs    = [0, 1, 4, 9, 31, 31, 41]
    sinit_regs    = [0, 1, 4, 9, 41]

    vinit_vals_rt = ['0xce', '0x2b', '0x7d', '0x5c']  # VDDA = 2.4V
    #vinit_vals_ln = ['0xda', '0x32', '0x86', '0x64']  # VDDA = 2.3V
    vinit_vals_ln = ['0xdc', '0x31', '0x87', '0x64']  # VDDA = 2.3V
    ref_volts     = [1.95, 0.45, 1.2, 0.9]
    ref_volts_regs= ['0b1101', '0b10001', '0b1001', '0b101']

    sinit_vals_di = ['0xa3', '0x0', '0x33', '0b1000', '0x1']
    sinit_vals_se = ['0x63', '0x0', '0x3b', '0b1000', '0x1']    

    autocalib_regs = [31, 31]
    autocalib_vals = ['0x3', '0x0']

    vdda_ps_ln    = 2.3
    vdda_ps_rt    = 2.5
    vdda_ps_chan  = 3 

    w0_def        = ['0xc000', '0xe000', '0xf000', '0xf800', '0xfc00', '0xfe00', '0xff00']
    w2_def        = ['0x4000', '0x2000', '0x1000', '0x0800', '0x0400', '0x0200', '0x0100']

    FPGA_FIFO_FULL=12
    UART_SEL=27
    ADC_RESET=6
    FPGA_RESET=22

    DNLSamples = 480
    NWORDFIFO=65536

    #GUI window defined entirely in init function
    def __init__(self, master=None,forceQuick=False,forceLong=False):
        Frame.__init__(self,master)
        self.pack()

#        self.config = CONFIG()

        if forceQuick and forceLong:
            raise Exception("Can't forceQuick and forceLong at the same time")
        self.forceQuick = forceQuick
        self.forceLong = forceLong

        self.timestamp = None
        self.result_labels = []
        self.display_procs = []
        #Define general commands column
        self.define_test_details_column()
        self.reset()

        self.master.protocol("WM_DELETE_WINDOW", self.exit)

        self.data_base_dir = "/home/dune/ColdADC/test_results"
        check_folder = os.path.isdir(self.data_base_dir)
        if not check_folder: os.makedirs(self.data_base_dir)

        self.soft_dir = os.environ["PWD"]



########### Single Test Methods ########################  

    def run_read(self):

        self.status_label.config(text="Running Reg Read Test")
        coldADC_regs=[0, 1, 4, 9, 41]
        coldADC_vals_di=['0xa3', '0x0', '0x33', '0x8', '0x1']
        coldADC_vals_se=['0x63', '0x0', '0x3b', '0x8', '0x1']
        coldADC_2ndP_regs=[1,2,3,4]
        coldADC_2ndP_vals=['0x10','0x4','0x0','0x0']
       
########## UART Read
        self.set_regcom('UART')

        for i in range(len(coldADC_regs)):
            regval = readReg(int(coldADC_regs[i]))
            if not ((str(hex(regval)) == coldADC_vals_di[i] and self.mode_val.get()==1) or (str(hex(regval)) == coldADC_vals_se[i] and self.mode_val.get()==2)):
                messagebox.showinfo(title="Failed", message="FAILED Reg {} using UART".format(coldADC_regs[i]))
                self.readtest_label.config(text=("FAILED Reg {} UART".format(coldADC_regs[i])))
                self.readregs_status = 'FAILED'
                return

#        for i in range(len(vdda_regs)):
#            regval = readReg(int(vdda_regs[i]))
#            if(str(hex(regval)) != vdda_vals_2p5[i]):
#                messagebox.showinfo(title="Failed", message="FAILED Reg {} using UART".format(coldADC_regs[i]))
#                self.readtest_label.config(text=("FAILED Reg {} UART".format(vdda_regs[i])))
#                self.readregs_status = 'FAILED'
#                return

######### Now I2C Read

        self.set_regcom('I2C')
        
        for i in range(len(coldADC_regs)):
            regval = readReg_i2c(1, int(coldADC_regs[i])+128)
            if not ((str(hex(regval)) == coldADC_vals_di[i] and self.mode_val.get()==1) or (str(hex(regval)) == coldADC_vals_se[i] and self.mode_val.get()==2)):
                messagebox.showinfo(title="Failed", message="FAILED Reg {} using I2C".format(coldADC_regs[i]))
                self.readtest_label.config(text=("FAILED Page 1 Reg {} I2C".format(coldADC_regs[i])))
                self.readregs_status = 'FAILED'
                return

#        for i in range(len(vdda_regs)):
#            regval = readReg_i2c(1, int(vdda_regs[i])+128)
#            if(str(hex(regval)) != vdda_vals_2p5[i]):
#                messagebox.showinfo(title="Failed", message="FAILED Reg {} using I2C".format(coldADC_regs[i]))
#                self.readtest_label.config(text=("FAILED Page 1 Reg {} I2C".format(vdda_regs[i])))
#                self.readregs_status = 'FAILED'
#                return

        for i in range(len(coldADC_2ndP_regs)):
            regval = readReg_i2c(2, int(coldADC_2ndP_regs[i]))
            if(str(hex(regval)) != coldADC_2ndP_vals[i]):
                self.readtest_label.config(text=("FAILED Page 2 Reg {} using I2C".format(coldADC_2ndP_regs[i])))
                self.readregs_status = 'FAILED'
                return

        self.readregs_status = 'PASSED'
        self.readtest_label.config(text=("PASSED"))
        self.status_label.config(text="Reg Read Test DONE")
        return self.readregs_status

    def read_calib(self, calibFname=None):

        if(calibFname==None):
            calibFname='calib_const.txt'

        calibFile = open(calibFname, "w")

        self.set_regcom('UART')
        calib_vals = readCalib()        
        outLine = "ADC, Stage, W0 Diff, W2 Diff\n"
        for ichip in range(0,2):
            for ist in range(0,7):

                ind = ichip*64 + ist*4

                w0 = int(calib_vals[ind+1])*256 + int(calib_vals[ind])
                w2 = int(calib_vals[ind+3])*256 + int(calib_vals[ind+2])

                calibFile.write("{}, {}, {}, {}, {}, {}\n".format(ichip, ist, hex(w0), hex(w0-int(self.w0_def[ist], 16)), hex(w2), hex(w2-int(self.w2_def[ist],16))))
                outLine = outLine + "  {},     {},     {},     {}\n".format(ichip, ist, hex(w0-int(self.w0_def[ist], 16)), hex(w2-int(self.w2_def[ist],16)))

        self.set_regcom('I2C')
        calibFile.close()
        messagebox.showinfo(title="Results", message=outLine)
        self.status_label.config(text="Read Calib Const Test DONE")
        return outLine

    def run_softreset(self):

        self.set_regcom('I2C')
        writeReg_i2c(2, 2, '0x05')
        #sleep (0.5)
        if (str(hex(readReg_i2c(2, 2)))!='0x5'):
            messagebox.showinfo(title="Failed", message="FAILED setting register 2 page 2!")
            return
    
        os.system('/home/dune/ColdADC/coldadc_qc_test/coldADC_SoftReset.py')
        sleep (0.5)
        if (str(hex(readReg_i2c(2, 2)))!='0x4'):
            messagebox.showinfo(title="Failed", message="FAILED reset register 2 page 2!")
            return
        self.resettest_label.config(text=("PASSED"))
        self.status_label.config(text="Soft Reset Test DONE")
        return  'PASSED'      

    def run_noise(self):

        self.status_label.config(text="Running Noise Test")

        ps_chan = 2
        v_ps_noise = 5.0

        self.gen_onoff('OFF')

        messagebox.showinfo(title="Action Needed", message="Please move the jumper boards for noise measurement and click OK when ready.")

        self.ps_interface.set_channel(ps_chan, float(v_ps_noise), None, None, float(0.5))
        sleep(1)
        self.ps_interface.on(ps_chan)
        sleep(1)

#        self.avgnoise = calc_noise()
        os.system('{}/qc_noise.py'.format(self.soft_dir))

        self.status_label.config(text="Noise Test DONE")
        self.ps_interface.off(ps_chan)

        messagebox.showinfo(title="Action Needed", message="Please move the jumper boards for generator and click OK when ready.")


        return 

    def run_1ch(self): 
        self.gen_onoff('ON')
        sleep (1)
        self.status_label.config(text="Running Single Channel")
        os.system('/home/dune/ColdADC/coldadc_qc_test/plotRamp.py')
        self.gen_onoff('OFF')
        sleep (1)
        self.status_label.config(text="1Ch Dynamic Test DONE")

    def run_16ch(self): 
        self.gen_onoff('ON')
        sleep (1)
        self.status_label.config(text="Running 16 Channels")
        os.system('{}/qc_fft_enob.py'.format(self.soft_dir))
        self.gen_onoff('OFF')
        sleep (1)
        self.status_label.config(text="16Ch Dynamic Test DONE")

    def run_linearity(self, dirsave='.', asicID=''):
        writeReg_i2c(2, 1, '0b01100')
        self.gen_onoff('ON')
        sleep (2)
        self.status_label.config(text="Running INL and DNL")
        spi = qc_dnl_inl_newer.initSPI()
        gport = qc_dnl_inl_newer.initGPIOpoll(self.FPGA_FIFO_FULL)
        rawLinData = qc_dnl_inl_newer.readNSamp( \
                gport, spi, self.FPGA_FIFO_FULL, self.NWORDFIFO, self.DNLSamples)
        #print(rawLinData)
        #np.savetxt(f'fast_deserialize_test/rawLinData_{asicID}.csv', rawLinData, fmt='%d', delimiter=',')
        qc_dnl_inl_newer.calc_plot_dnl_inl(rawLinData, dirsave, asicID, self.DNLSamples)
        del rawLinData
        spi.close()
        gport.cleanup
        self.status_label.config(text="INL and DNL DONE")
        self.gen_onoff('OFF')
        writeReg_i2c(2, 1, '0b10000')
        #sleep (1)

########## QC Procedure Method #####################################

    def run_qc(self):
        if(len(self.asic_entries[0].get())==0 or len(self.operator_entry.get())==0 or len(self.boardid_entry.get())==0):
            messagebox.showinfo(title="Missing Information", message="Please fill in the empty fields!")
            return

        self.coldadc_ID = self.asic_entries[0].get()
        print("QC Test Report ColdADC: {} {}".format(self.boardid_entry.get(), self.coldadc_ID))
        self.get_options()

        ############ Power Cycle and Initialize the ASIC
        self.init_board_qc()
        #self.read_calib()
        #sleep(10)
        self.sel_se_diff('DIFF')
        #self.read_calib()
        endtime = time()
        print(f'TIME ELAPSED: {endtime - MYTIME}')
        self.run_autocalib()
        self.read_calib()

        if(self.temp_val.get()==1):
            qc_temp = 'ROOM'
            temp_sel = 'rt'
            vdda_qc = float(self.vdda_ps_rt)
        elif(self.temp_val.get()==2):
            qc_temp = 'LIQUID NITROGEN'
            temp_sel = 'ln'
            vdda_qc = float(self.vdda_ps_ln)

        ############ Adjust Reference Voltages to Default
        refvset = self.set_ref_voltages()  
        self.read_calib()

        messagebox.showinfo(title="Action Needed", message="Please check that both red and green LEDs are ON at the back of the SRS generator. If not, please reconnect the BNC sync cable.")

        self.status_label.config(text="Running QC Test")
        self.dirsave = "{}/coldadc_{}_{}_{}_{}".format(self.data_base_dir, self.boardid_entry.get(), self.coldadc_ID, temp_sel, self.timestamp)
        check_folder = os.path.isdir(self.dirsave)
        if not check_folder: os.makedirs(self.dirsave)
        filename="{}_{}_{}".format(self.boardid_entry.get(), self.asic_entries[0].get(), temp_sel)
     
        repFilename = "{}/test_report_COLDADC_{}.txt".format(self.dirsave, filename)
        reportFile=open(repFilename, "w")
        reportFile.write("QC Test Report ColdADC for ASIC with SN {} {} \n\n".format(self.boardid_entry.get(), self.coldadc_ID))
        reportFile.write("Operator Name: {}\n".format(self.operator_entry.get()))
        reportFile.write("Test Results Folder: {} \n\n".format(self.dirsave))
        print("Test Results Folder: {}\n".format(self.dirsave))

        reportFile.write("Testing Temperatura: {}\n".format(qc_temp))
        reportFile.write("Communication Mode: I2C\n")
        reportFile.write("Input Signal: DIFFERENTIAL\n")

        reportFile.write("Reference Voltages: \n {}\n".format(refvset))

        readreg = self.run_read() 
        print("Registers Read Test: {}\n".format(readreg))
        reportFile.write("Registers Read Test: {}\n\n".format(readreg))
   
        readcalib = self.read_calib("{}/ColdADC_{}_calib_const.csv".format(self.dirsave,filename))
        print("Read Calibration Weights:\n {}\n\n".format(readcalib))
        reportFile.write("Read Calibration Weights: \n {}\n\n".format(readcalib))
     
        runsoftrst = self.run_softreset()
        print("Soft Reset Test: {}\n".format(runsoftrst))
        reportFile.write("Soft Reset Test: {}\n\n".format(runsoftrst))

#        if (abs(float(self.read_vdda('v')))==0):
        '''
        if (self.ps_interface.get_on_off(self.vdda_ps_chan) == False):


            self.vdda_onoff('ON')
            print("External VDDA Voltage: {} V\n".format(self.read_vdda('v')))
            reportFile.write("External VDDA Voltage: {} V\n\n".format(self.read_vdda('v')))
            print("External VDDA Power DIFF mode: {} W\n\n".format(self.read_vdda('p')))
            reportFile.write("External VDDA Power DIFF mode: {} W\n\n".format(self.read_vdda('p')))
            if float(self.read_vdda('p'))>0.4:
                messagebox.showinfo(title="Warning", message="High VDDA power comsumption("+str(elf.read_vdda('p'))+")")
            self.sel_se_diff('SE')
            print("External VDDA Power SE mode: {} W\n\n".format(self.read_vdda('p')))
            reportFile.write("External VDDA Power SE mode: {} W\n\n".format(self.read_vdda('p')))
            if float(self.read_vdda('p'))>0.4:
                messagebox.showinfo(title="Warning", message="High VDDA power comsumption("+str(elf.read_vdda('p'))+")")
            self.vdda_onoff('OFF')
        else:
        '''
        v = float(self.read_vdda('v'))
        print(f"External VDDA Voltage: {v} V\n")
        reportFile.write(f"External VDDA Voltage: {v} V\n\n")
        p = float(self.read_vdda('p'))
        print(f"External VDDA Power DIFF: {p} W\n")
        reportFile.write(f"External VDDA Power DIFF: {p} W\n\n")
        if p > 0.4:
            messagebox.showinfo(title="Warning", message="High VDDA power comsumption("+str(p)+")")
        self.sel_se_diff('SE')
        p = float(self.read_vdda('p'))
        print(f"External VDDA Power SE mode: {p} W\n\n")
        reportFile.write(f"External VDDA Power SE mode: {p} W\n\n")
        if p > 0.4:
            messagebox.showinfo(title="Warning", message="High VDDA power comsumption("+str(p)+")")
       
        self.sel_se_diff('DIFF')
        print(self.dirsave, filename)

        reportFile.close()

        vddaFilename = "{}/ColdADC_VDDA_{}.csv".format(self.dirsave, filename)
        vddaFile=open(vddaFilename, "w")
        vddaFile.write(refvset)
        vddaFile.close()

        ############# Setup PS Channel 2 for noise measurement
        ps_chan = 2
        v_ps_noise = 5.0
        ############# Turn off the generator
        self.gen_onoff('OFF')
        messagebox.showinfo(title="Action Needed", message="Please move the jumper boards for noise measurement and click OK when ready.")

        ############# Set voltage and turn on PS channel2
        self.ps_interface.set_channel(ps_chan, float(v_ps_noise), None, None, float(0.5))
        sleep(0.5)
        self.ps_interface.on(ps_chan)
        sleep(0.5)

        ############# Measure Noise in differential mode
        os.system("{}/qc_noise.py {} {} >> {}".format(self.soft_dir,self.dirsave, filename+'_DIFF', repFilename))
#        self.avgnoise = calc_noise()


        ############# Measure noise in single-ended mode
        self.sel_se_diff('SE')
        os.system("{}/qc_noise.py {} {} >> {}".format(self.soft_dir,self.dirsave, filename+'_SE', repFilename))

        self.status_label.config(text="Noise Test DONE")
 
        ############ Turn off PS channel 2
        self.ps_interface.off(ps_chan)

        messagebox.showinfo(title="Action Needed", message="Please move the jumper boards for generator and click OK when ready.")

        #############  Measure DNL/INL at LN2
        if(self.temp_val.get()==2 or self.warmonly.get()==1):        

            # Differential mode
            self.sel_se_diff('DIFF')
            self.run_linearity(self.dirsave, filename + '_DIFF')
            #############  Single-Ended Mode
            self.sel_se_diff('SE')
            self.run_linearity(self.dirsave, filename + '_SE')

        ############## Measure ENOB, SNR, THD, etc.
        self.sel_se_diff('DIFF')
        self.gen_onoff('ON')
        sleep(1)
        os.system("{}/qc_fft_enob.py {} {} >> {}".format(self.soft_dir,self.dirsave, filename, repFilename))
##        fftstat = calc_fft(self.dirsave, filename)
        self.status_label.config(text="16ch Dynamic Test DONE")

        checkifgood = messagebox.askyesno(title="Confirmation", message="Are the ENOB, SNR, THD, and noise plots as expected?")
        if not checkifgood:
            messagebox.showinfo(title="Warning", message="Exiting QC Test. TEST FAILED!") 
            return

        self.gen_onoff('OFF')
        self.status_label.config(text="QC Test DONE")
        messagebox.showinfo(title="Information", message="ColdADC QC Test Has Finished")
        self.ldo_off()
        
        messagebox.showinfo(title='Information', message='Please Start Warming Up.')

#        if(noistat and fftstat and dnlstat):
#            self.qctest_label.config(text=("PASSED"))
#            messagebox.showinfo(title="Result", message="ColdADC {} has passed the QC tests!".format(self.coldadc_ID))

#        os.system("gpicview {}".format(self.dirsave))
#        self.reset()

########## Read Single Register ########################

    def read_reg(self):

        if not self.regnum_entry.get():
            messagebox.showinfo(title="Missing Information", message="Please fill in the register number!")
            return

        regnum = int(self.regnum_entry.get())
        
        if self.comm_mode["text"] == "Comm Mode: UART":
            regval = readReg(regnum)
        elif self.comm_mode["text"] == "Comm Mode: I2C":
            if not self.regpage_entry.get():
                messagebox.showinfo(title="Missing Information", message="Using I2C! Please fill in the page number!")
                return
            pagenum = int(self.regpage_entry.get())
            if pagenum != 1 and pagenum != 2:
                messagebox.showinfo(title="Invalid Entry!", message="Register page is either 1 or 2!")
                return
            elif pagenum == 1:
                regnum = regnum + 128

            regval = readReg_i2c(pagenum,regnum)         

        self.regval_label.config(text=hex(regval))
        return hex(regval)

########## Method for Iterative Setup of ColdADC Reference Voltages ##########

    def set_ref_voltages(self):
        # trying different thing
        if self.temp_val.get() == 2:
            vdda_ps = self.vdda_ps_ln
        else:
            vdda_ps = self.vdda_ps_rt
        # end new thing
        self.set_regcom('I2C')
        outLine = "Register,  Reg Value, Meas Voltage (V)\n"
        for i in range(len(self.vinit_regs)):
            writeReg_i2c(1, int(47)+128, self.ref_volts_regs[i])
            sleep(1)
            #sleep (0.5)
            curr_volt = 0
            corrVal = 5
    
            while corrVal>1:
                readV = 0.3
                count = 0
                while readV>0.2:
                    curr_volt = readVolts()
                    sleep (1)
                    readV = abs(curr_volt - self.ref_volts[i])
                    count += 1
                    if count > 4:
                        break

                #corrVal = (self.ref_volts[i] - curr_volt)/self.vdda_ps_ln*256
                corrVal = (self.ref_volts[i] - curr_volt)/vdda_ps*256
                old_regval = readReg_i2c(1, int(self.vinit_regs[i])+128)

                new_regval = (int(old_regval)+int(corrVal))
                if (new_regval>255): new_regval = 255

                print("Correction: {:2.3}; Old reg value {}; New regs value: {}\n".format(corrVal, hex(old_regval), hex(new_regval)))
                writeReg_i2c(1, int(self.vinit_regs[i])+128, hex(new_regval))
                #sleep(0.5)
                
                '''why is this here???
                readV = 0.3
                count = 0
                while readV>0.2:
                    curr_volt = readVolts()
                    sleep (1)
                    readV = abs(curr_volt - self.ref_volts[i])
                    count += 1
                    if count > 4:
                        break
                '''
                            
            print('Current reading: {}V'.format(curr_volt))
            if(i==0): 
                self.vrefp_val["text"]='{:2.3} V'.format(curr_volt)
                self.vrefp_reg["text"]='Reg {}: {}'.format(self.vinit_regs[i], hex(new_regval))
                outLine = outLine + "  {},       {},         {:2.3} \n".format(self.vinit_regs[i], hex(new_regval), curr_volt)
            if(i==1):
                self.vrefn_val["text"]='{:2.3} V'.format(curr_volt)
                self.vrefn_reg["text"]='Reg {}: {}'.format(self.vinit_regs[i], hex(new_regval))
                outLine = outLine + "  {},       {},         {:2.3} \n".format(self.vinit_regs[i], hex(new_regval), curr_volt)
            if(i==2):
                self.vcmo_val["text"]='{:2.3} V'.format(curr_volt)
                self.vcmo_reg["text"]='Reg {}: {}'.format(self.vinit_regs[i], hex(new_regval))
                outLine = outLine + "  {},       {},         {:2.3} \n".format(self.vinit_regs[i], hex(new_regval), curr_volt)
            if(i==3):
                self.vcmi_val["text"]='{:2.3} V'.format(curr_volt)
                self.vcmi_reg["text"]='Reg {}: {}'.format(self.vinit_regs[i], hex(new_regval))
                outLine = outLine + "  {},       {},         {:2.3} \n".format(self.vinit_regs[i], hex(new_regval), curr_volt)
        return outLine

    def meas_ref_voltages(self):
        self.set_regcom('I2C')
        for i in range(len(self.vinit_regs)):
            writeReg_i2c(1, int(47)+128, self.ref_volts_regs[i])
            sleep(1)
            #sleep (0.5)
            curr_volt = 0

            readV = 0.3
            count = 0
            while readV>0.2:
                curr_volt = readVolts()
                sleep (1)
                readV = abs(curr_volt - self.ref_volts[i])
                count += 1
                if count > 4:
                    break

            regval = hex(int(readReg_i2c(1, int(self.vinit_regs[i])+128)))
            if(i==0):
                self.vrefp_val["text"]='{:2.3} V'.format(curr_volt)
                self.vrefp_reg["text"]='Reg {}: {}'.format(self.vinit_regs[i], regval)
            if(i==1):
                self.vrefn_val["text"]='{:2.3} V'.format(curr_volt)
                self.vrefn_reg["text"]='Reg {}: {}'.format(self.vinit_regs[i], regval)
            if(i==2):
                self.vcmo_val["text"]='{:2.3} V'.format(curr_volt)
                self.vcmo_reg["text"]='Reg {}: {}'.format(self.vinit_regs[i], regval)
            if(i==3):
                self.vcmi_val["text"]='{:2.3} V'.format(curr_volt)
                self.vcmi_reg["text"]='Reg {}: {}'.format(self.vinit_regs[i], regval)


########## Generator Setup Methods ######################

    def set_generator(self):

        self.gen_onoff('OFF')

        if not self.genampl_entry.get():
            ampl = 1.4
        else:
            ampl = float(self.genampl_entry.get())
            if ampl>1.8 or ampl<0:
                ampl = 1.4
        self.srs_interface.setAmpl(ampl)               

        if not self.genoffs_entry.get():
            offs = 0.9
        else:
            offs = float(self.genoffs_entry.get())
            if offs>1.2 or offs<0:
                offs = 0.9
        self.srs_interface.setOffset(offs)

        if not self.genfreq_entry.get():
            freq = 147460
        else:
            freq = float(self.genfreq_entry.get())
            if freq>200000 or freq<0.01:
                freq = 147460        
        self.srs_interface.setFreq(freq)

        self.gen_onoff('ON')

    def gen_onoff(self, usett=None):

        state = self.srs_interface.checkStatus()
        if usett != None:
            state = -1

        if (state==1 or usett == 'OFF'):
            self.srs_interface.turnOFF()
        elif (state==0 or usett == 'ON'):
            self.srs_interface.turnON()

        self.gen_state()


    def gen_state(self):
        self.gen_stat["text"]="Gen: A={}V; O={}V; F={}Hz".format(self.srs_interface.getAmpl(),self.srs_interface.getOffset(),self.srs_interface.getFreq())
        if self.srs_interface.checkStatus():
            self.genstat_label["text"]="State: ON"    
        else:
            self.genstat_label["text"]="State: OFF"

############ External VDDA Setup Methods #############################

    def set_vdda(self, vdda_u = None):
        '''Sets external power supply VDDA'''
        #self.vdda_onoff('OFF')
        vdda_ps = self.vdda_ps_rt
        if not self.vddaampl_entry.get():
            if self.temp_val.get()==1:    
                vdda_ps = self.vdda_ps_rt
            elif self.temp_val.get()==2:
                vdda_ps = self.vdda_ps_ln
        else:
            if float(self.vddaampl_entry.get())<0 or float(self.vddaampl_entry.get())>3:
                vdda_ps = self.vdda_ps_rt
            else:
                vdda_ps=float(self.vddaampl_entry.get())
        if (vdda_u != None and float(vdda_u)>0 and float(vdda_u)<3):
            vdda_ps = vdda_u
        print("Ext VDDA PS set to: {}".format(vdda_ps))
        self.ps_interface.set_channel(self.vdda_ps_chan, float(vdda_ps), None, None, float(0.5))
        return

    def vdda_onoff(self, state=None):

        vdda_sel = self.vdda_val.get()
        if state != None:
            vdda_sel = 0

        if(vdda_sel == 1 or state=='ON'):
            os.system('/home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/coldADC_VDDA_off.py')
            sleep(1)
            self.ps_interface.on(self.vdda_ps_chan)
            sleep(1)
        elif(vdda_sel == 2 or state=='OFF'):
            self.ps_interface.off(self.vdda_ps_chan)
            sleep(1)
            os.system('/home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/coldADC_VDDA_on.py')
            sleep(1)   
        return self.read_vdda('v')
        
    def read_vdda(self, quant):
        print("Reading Channel " + str(self.vdda_ps_chan))
        if (quant == 'v'):
            reading = self.ps_interface.measure_voltage(self.vdda_ps_chan)
#            print(self.ps_interface.get_on_off(self.vdda_ps_chan))
            print(reading)
            self.test_vdda.config(text=("Ext VDDA: {} V".format(reading)))
            return reading
        elif (quant == 'p'):
            return self.ps_interface.measure_power(self.vdda_ps_chan)
        self.test_vdda["state"] = "normal"
        return None

    def read_anpow(self):
        power = self.read_vdda('p')
        self.anpow_label.config(text=("{:2.3} W".format(power)))
        return power

############# ColdADC Communication Method (UART or I2C) #####################

    def set_regcom(self, usett=None):
        com_val = self.regcom_val.get()
        if usett != None:
            com_val = 0

        if (com_val == 1 or usett=='UART'):
            self.comm_mode["text"] = "Comm Mode: UART"
            os.system('/home/dune/ColdADC/coldadc_qc_test/coldADC_uartsel.py')
        elif (com_val == 2 or usett=='I2C'):
            self.comm_mode["text"] = "Comm Mode: I2C"
            os.system('/home/dune/ColdADC/coldadc_qc_test/coldADC_i2csel.py')

    def sel_se_diff(self, inp_s = None):

        self.set_regcom('I2C')
        sig_mode = self.mode_val.get()
        if inp_s != None:
            sig_mode = 0

        if(sig_mode == 1 or inp_s == 'DIFF'):
            self.test_mode.config(text="TEST MODE: DIFFERENTIAL")
            for i in range(len(self.sinit_regs)):
                writeReg_i2c(1, int(self.sinit_regs[i])+128, self.sinit_vals_di[i])
                #sleep (0.5)
            self.mode_val.set(1)
        elif(sig_mode == 2 or inp_s == 'SE'):
            self.test_mode.config(text="TEST MODE: SINGLE-ENDED")
            for i in range(len(self.sinit_regs)):
                writeReg_i2c(1, int(self.sinit_regs[i])+128, self.sinit_vals_se[i])
                #sleep (0.5)
            self.mode_val.set(2)

    def run_autocalib(self):
        for i in range(len(self.autocalib_regs)):
            writeReg_i2c(1, int(self.autocalib_regs[i])+128, self.autocalib_vals[i])
            sleep(0.5)

############# Initialization of Test Board and ColdADC #########################

    def init_board_i2c(self):
        self.init_board_qc()
        '''
        self.ldo_off()
        sleep (1)
        os.system('/home/dune/ColdADC/coldadc_qc_test/coldADC_resetFPGA.py')
        sleep (1)
        oscommand = "/home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/coldADC_ldo_on.py"
        sleep (1)
        os.system(oscommand)
        os.system('/home/dune/ColdADC/coldadc_qc_test/coldADC_resetADC_i2c.py')
        sleep (1)
        self.set_regcom('I2C')


        if(self.temp_val.get()==1):
            self.test_temp.config(text="TEMP: ROOM")
            for i in range(len(self.vinit_regs)):
                writeReg_i2c(1, int(self.vinit_regs[i])+128, self.vinit_vals_rt[i])
                #sleep (0.5)
        elif(self.temp_val.get()==2):
            self.test_mode.config(text="TEMP: LN2")
            os.system('/home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/coldADC_i2c_VDDA_off.py')
            sleep (1)
            self.set_vdda(float(self.vdda_ps_ln))
            sleep (1)
            self.vdda_onoff('ON')
            sleep (1)
            for i in range(len(self.vinit_regs)):
                writeReg_i2c(1, int(self.vinit_regs[i])+128, self.vinit_vals_ln[i])
                #sleep (0.5)
        '''

        self.meas_ref_voltages()
        #self.set_ref_voltages()
            
        if(self.mode_val.get()==1):
            self.test_mode.config(text="TEST MODE: DIFFERENTIAL")
            for i in range(len(self.sinit_regs)):
                writeReg_i2c(1, int(self.sinit_regs[i])+128, self.sinit_vals_di[i])
                #sleep (0.5)
        elif(self.mode_val.get()==2):
            self.test_mode.config(text="TEST MODE: SINGLE-ENDED")
            for i in range(len(self.sinit_regs)):
                writeReg_i2c(1, int(self.sinit_regs[i])+128, self.sinit_vals_se[i])
                #sleep (0.5)

        self.power_check.deselect()
        self.warmonly_check.deselect()
        self.prepare_button.config(state="disable")
        self.readtest_button["state"]  = "normal"
        self.chantest_button["state"]  = "normal"
        self.ch16test_button["state"]  = "normal"
        self.noistest_button["state"]  = "normal"
        self.linrtest_button["state"]  = "normal"
        self.readreg_button["state"]   = "normal"
        #self.qctest_button["state"]    = "normal"
        self.setvdda_button["state"]   = "normal"
        self.regcom_button["state"]    = "normal"
        self.resettest_button["state"] = "normal"
        self.readcal_button["state"]   = "normal"
        self.measrefv_button["state"]  = "normal"
        self.adjrefv_button["state"]   = "normal"
        #self.gen_onoff('OFF')

   
    def init_board_qc(self):
        global MYTIME   # DEBUG
        self.ps_interface.off(self.vdda_ps_chan)
        sleep (1)        
        os.system('/home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/coldADC_ldo_off.py')
        sleep (3)
        os.system('/home/dune/ColdADC/coldadc_qc_test/coldADC_resetFPGA.py')
        sleep (1)
        os.system('/home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/coldADC_VDDD_on.py')
        MYTIME = time()
        sleep(3)   # DEBUG
        sleep (1)
        os.system('/home/dune/ColdADC/coldadc_qc_test/coldADC_resetADC_i2c.py')
        sleep (1)
        self.set_regcom('I2C')
        #self.set_vdda(float(self.vdda_ps_rt))
        #self.vdda_onoff('ON')
        self.set_vdda()     # it should autodetect temp
        self.ps_interface.on(self.vdda_ps_chan)
        #sleep (1)
        if self.temp_val.get() == 1:
            self.test_temp.config(text="TEMP: ROOM")
            init_vals = self.vinit_vals_rt
        else:
            self.test_mode.config(text="TEMP: LN2")
            init_vals = self.vinit_vals_ln
        for i in range(len(self.vinit_regs)):
            writeReg_i2c(1, int(self.vinit_regs[i])+128, init_vals[i])
        self.read_vdda('v')


    def init_board_uart(self):

        vddachan = 3
        self.ps_interface.off(vddachan)
        sleep(3)        
        self.set_regcom('UART')

        print(self.temp_val.get(), self.mode_val.get())
        if(self.temp_val.get()==1 and self.mode_val.get()==1):
            os.system('/home/dune/ColdADC/coldadc_qc_test/init_ColdADC_room_diff.sh')
            self.test_temp.config(text="TEMP: ROOM")
            self.test_mode.config(text="TEST MODE: DIFFERENTIAL")
        
        elif(self.temp_val.get()==2 and self.mode_val.get()==1):
            os.system('/home/dune/ColdADC/coldadc_qc_test/init_ColdADC_LN2_diff.sh')
            self.test_temp.config(text="TEMP: LN2")
            self.test_mode.config(text="TEST MODE: DIFFERENTIAL")

        elif(self.temp_val.get()==1 and self.mode_val.get()==2):
#            os.system('/home/dune/ColdADC/init_ColdADC_room_diff.sh')
            self.test_temp.config(text="TEMP: ROOM")
            self.test_mode.config(text="TEST MODE: SINGLE-ENDED")

        elif(self.temp_val.get()==2 and self.mode_val.get()==2):
#            os.system('/home/dune/ColdADC/init_ColdADC_room_diff.sh')
            self.test_temp.config(text="TEMP: LN2")
            self.test_mode.config(text="TEST MODE: SINGLE-ENDED")
        else:
            self.power_check.deselect()
            self.prepare_button.config(state="disable")
            return

#        if(self.read_vdda('v') > 0):
        if(self.ps_interface.get_on_off(self.vdda_ps_chan) == True):
            os.system('/home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/coldADC_VDDA_off.py')

        self.power_check.deselect()
        self.warmonly_check.deselect()
        self.prepare_button.config(state="disable")
        self.readtest_button["state"]  = "normal"
        self.chantest_button["state"]  = "normal"
        self.ch16test_button["state"]  = "normal"
        self.noistest_button["state"]  = "normal"
        self.linrtest_button["state"]  = "normal"
        self.readreg_button["state"]   = "normal"
        #self.qctest_button["state"]    = "normal"
        self.setvdda_button["state"]   = "normal"
        self.regcom_button["state"]    = "normal"
        self.resettest_button["state"] = "normal"
        self.readcal_button["state"]   = "normal"
        self.set_generator()

############# Various GUI Control Methods ############################

    def ena_disa(self):
        if(self.powercheck.get()):self.prepare_button.config(state="normal")
        else:self.prepare_button.config(state="disabled")

        if(self.resetcheck.get()):self.reset_button.config(state="normal")
        else:self.reset_button.config(state="disable")

    def ldo_off(self):
      
        self.ps_interface.off(self.vdda_ps_chan)        
        sleep (1)

        oscommand = "/home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/coldADC_ldo_off.py" 
        os.system(oscommand)
        sleep (2)

        self.readtest_button["state"]  = "normal"
        self.chantest_button["state"]  = "normal"
        self.ch16test_button["state"]  = "normal"
        self.noistest_button["state"]  = "normal"
        self.linrtest_button["state"]  = "normal"
        self.readreg_button["state"]   = "normal"
        self.readreg_button["state"]   = "normal"
        self.reset_button["state"]     = "normal"
        #self.qctest_button["state"]    = "normal"
        self.setvdda_button["state"]   = "normal"
        self.regcom_button["state"]    = "normal"
        self.resettest_button["state"] = "normal"
        self.readcal_button["state"]   = "normal"
        self.measrefv_button["state"]  = "normal"
        self.adjrefv_button["state"]   = "normal"
        self.reset_check.deselect()
        self.warmonly_check.deselect()
        #self.gen_onoff('OFF')
        self.read_vdda('v')

    def define_test_details_column(self):


#######  Setting Up Bottom Status Bar ############################
        columnbase=0
#        self.runid_label = Label(self, text="")
#        self.runid_label.grid(row=112,column=columnbase,columnspan=2,pady=10)

        self.status_label = Label(self, text="NOT STARTED",bd=1,relief=SUNKEN,width=25)
        self.status_label.grid(row=1000,column=columnbase,columnspan=1)
        self.bkg_color = self.status_label.cget("background")

        self.test_mode = Label(self, text="TEST MODE: ",bd=1,relief=SUNKEN,width=25)
        self.test_mode.grid(row=1000,column=columnbase+1,columnspan=1)
        self.bkg_color = self.test_mode.cget("background")

        self.test_temp = Label(self, text="TEMP: ",bd=1,relief=SUNKEN,width=15)
        self.test_temp.grid(row=1000,column=columnbase+2,columnspan=1)
        self.bkg_color = self.test_temp.cget("background")

        self.test_vdda = Label(self, text="Ext VDDA: ",bd=1,relief=SUNKEN,width=15)
        self.test_vdda.grid(row=1000,column=columnbase+3,columnspan=1)
        self.bkg_color = self.test_vdda.cget("background")

        self.comm_mode = Label(self, text="Comm Mode: ",bd=1,relief=SUNKEN,width=15)
        self.comm_mode.grid(row=1000,column=columnbase+4,columnspan=1)
        self.bkg_color = self.comm_mode.cget("background")

        self.gen_stat = Label(self, text="Fun Gen: A={}V; O={}V; F={}Hz".format('','',''),bd=1,relief=SUNKEN,width=40)
        self.gen_stat.grid(row=1000,column=columnbase+5,columnspan=3)
        self.bkg_color = self.gen_stat.cget("background")


#######  Testing Options Section

        self.sec1_label = Label(self,text="Tests",width=15)
        self.sec1_label.grid(sticky=W,row=1,column=columnbase+1)

        # Adding operator name label and read entry box
        self.operator_label = Label(self,text="Operator Name:",width=25)
        self.operator_label.grid(sticky=W,row=3,column=columnbase+0)

        self.operator_entry = Entry(self,width=20)
        self.operator_entry.grid(sticky=W,row=3,column=columnbase+1)

        # Adding electronics ID and read entry box
        self.boardid_label = Label(self,text="Test Board ID:",width=25)
        self.boardid_label.grid(sticky=W,row=4,column=columnbase+0)

        self.boardid_entry = Entry(self,width=20)
        self.boardid_entry.grid(sticky=W,row=4,column=columnbase+1)

        # ASIC IDs
        self.asic_entries = []
        self.asic_labels = []
        for i in range(0,1):
            label = Label(self,text="ASIC {} ID:".format(i),width=25)
            label.grid(sticky=W,row=5+i,column=columnbase+0)

            asic_entry = Entry(self,width=20)
            asic_entry.grid(sticky=W,row=5+i,column=columnbase+1)

            self.asic_labels.append(label)
            self.asic_entries.append(asic_entry)
        
        # Adding electronics ID and read entry box
        self.readtest_button = Button(self, text="Regs Read Test", command=self.run_read, width=20)
        self.readtest_button.grid(row=51,column=columnbase+0,columnspan=1)
        self.readtest_label = Label(self, text="",bd=1,relief=SUNKEN,width=15)
        self.readtest_label.grid(sticky=W, row=51,column=columnbase+1)

        self.resettest_button = Button(self, text="Soft Reset Test", command=self.run_softreset, width=20)
        self.resettest_button.grid(row=52,column=columnbase+0,columnspan=1)
        self.resettest_label = Label(self, text="",bd=1,relief=SUNKEN,width=15)
        self.resettest_label.grid(sticky=W, row=52,column=columnbase+1)

        self.readcal_button = Button(self, text="Calib Constants", command=self.read_calib, width=20)
        self.readcal_button.grid(row=53,column=columnbase+0,columnspan=1)
#        self.readcal_label = Label(self, text="",bd=1,relief=SUNKEN,width=15)
#        self.readcal_label.grid(sticky=W, row=53,column=columnbase+1)

        self.chantest_button = Button(self,text="Ch1 Read Test", command=self.run_1ch, width=20)
        self.chantest_button.grid(row=54,column=columnbase+0)

        self.ch16test_button = Button(self,text="16Ch Dynamic Test", command=self.run_16ch, width=20)
        self.ch16test_button.grid(row=55,column=columnbase+0)
#        self.current_entry = Entry(self,width=25,state="disabled")
#        self.current_entry.grid(sticky=W,row=105,column=columnbase+1)

        self.noistest_button = Button(self, text="Noise Tests", command=self.run_noise, width=20)
        self.noistest_button.grid(row=56,column=columnbase+0)

        self.linrtest_button = Button(self, text="DNL and INL test", command=self.run_linearity, width=20)
        self.linrtest_button.grid(row=57,column=columnbase+0)

        self.qctest_button = Button(self, text="QC Test", command=self.run_qc, width=20)
        self.qctest_button.grid(row=58,column=columnbase+0,columnspan=1)
#        self.qctest_label = Label(self, text="",bd=1,relief=SUNKEN,width=15)
#        self.qctest_label.grid(sticky=W, row=58,column=columnbase+1)
#        self.separ_col2 = Separator(self, orient=VERTICAL)
#        self.separ_col2.grid(column=columnbase+2)
        self.warmonly_label = Label(self, text="Warm Only",bd=1,width=15)
        self.warmonly_label.grid(sticky=W, row=58,column=columnbase+1)
        self.warmonly=IntVar(self)
        self.warmonly_check = Checkbutton(self, variable=self.warmonly, onvalue=1, offvalue=0, command=self.warmonly.get())
        self.warmonly_check.grid(sticky=W, row=58, column=columnbase+1)


        self.regpage_label = Label(self, text="Reg Page", width=20)
        self.regpage_label.grid(sticky=W, row=60,column=columnbase+0, columnspan=1)
        self.regnum_label = Label(self, text="Reg Number", width=20)
        self.regnum_label.grid(sticky=W, row=61,column=columnbase+0, columnspan=1)
        self.regval_label = Label(self, text="Reg Value", width=20)
        self.regval_label.grid(sticky=W, row=62,column=columnbase+0, columnspan=1)

        self.regpage_entry = Entry(self,width=15)
        self.regpage_entry.grid(sticky=W,row=60,column=columnbase+1)
        self.regnum_entry = Entry(self,width=15)
        self.regnum_entry.grid(sticky=W,row=61,column=columnbase+1)
        self.regval_label = Label(self, text="",bd=1,relief=SUNKEN,width=15)
        self.regval_label.grid(sticky=W, row=62,column=columnbase+1)
        self.readreg_button = Button(self, text="Get Reg Value", command=self.read_reg, width=20)
        self.readreg_button.grid(sticky=W, row=63,column=columnbase+0,columnspan=1)



####### Testing Conditions

        self.prepare_button = Button(self, text="Initialize Board", command=self.init_board_i2c, width=10)
        self.prepare_button.grid(sticky=W, row=3,column=columnbase+2 ,columnspan=1)
        self.powercheck=IntVar(self)
        self.power_check = Checkbutton(self, variable=self.powercheck, onvalue=1, offvalue=0, command=self.ena_disa)
        self.power_check.grid(sticky=W, row=3, column=columnbase+3)

        self.reset_button = Button(self, text="POWER OFF", command=self.ldo_off, width=10,bg="#FF8000")
        self.reset_button.grid(sticky=W, row=4,column=columnbase+2,columnspan=1)
        self.resetcheck=IntVar(self)
        self.reset_check = Checkbutton(self, variable=self.resetcheck, onvalue=1, offvalue=0, command=self.ena_disa)
        self.reset_check.grid(sticky=W, row=4, column=columnbase+3)

        self.regcom_val=IntVar(self)
        self.comuart_button = Radiobutton(self, text="UART", variable = self.regcom_val, value = 1, command=self.regcom_val.get(), width=10)
        self.comuart_button.grid(sticky=W,row=50,column=columnbase+3)
        self.comi2c_button = Radiobutton(self, text="I2C", variable = self.regcom_val, value = 2, command=self.regcom_val.get(), width=10)
        self.comi2c_button.grid(sticky=W, row=50,column=columnbase+4)
        self.regcom_button = Button(self, text="Reg Comm", command=self.set_regcom, width=10)
        self.regcom_button.grid(sticky=W, row=50,column=columnbase+2,columnspan=1)


########  Test condition settings

        self.temp_val=IntVar(self)
        self.temp_label = Label(self, text="TEST TEMP", width=15)
        self.temp_label.grid(sticky=W, row=52,column=columnbase+2, columnspan=1)
        self.room_button = Radiobutton(self, text="Room Temp", variable = self.temp_val, value = 1, command=self.temp_val.get(), width=10)
        self.room_button.grid(sticky=W,row=52,column=columnbase+3)
        self.cryo_button = Radiobutton(self, text="LN2 Temp", variable = self.temp_val, value = 2, command=self.temp_val.get(), width=10)
        self.cryo_button.grid(sticky=W, row=52,column=columnbase+4)

        self.mode_val=IntVar(self)
        self.mode_label = Label(self, text="TEST MODE", width=15)
        self.mode_label.grid(sticky=W, row=53,column=columnbase+2)
        self.diffmo_button = Radiobutton(self, text="Differential", variable = self.mode_val, value = 1, command=self.mode_val.get(), width=10)
        self.diffmo_button.grid(sticky=W,row=53,column=columnbase+3)
        self.sinend_button = Radiobutton(self, text="Single Ended", variable = self.mode_val, value = 2, command=self.mode_val.get(), width=10)
        self.sinend_button.grid(sticky=W, row=53,column=columnbase+4)


#        self.refv_label = Label(self, text="Measured Reference Voltages", width=30)
#        self.refv_label.grid(sticky=W, row=55,column=columnbase+2, columnspan=3)

        self.measrefv_button = Button(self, text="Measure RefV", command=self.meas_ref_voltages, width=10)
        self.measrefv_button.grid(sticky=W, row=55,column=columnbase+3)
        self.adjrefv_button = Button(self, text="Adjust RefV", command=self.set_ref_voltages, width=10)
        self.adjrefv_button.grid(sticky=W, row=55,column=columnbase+4)

        self.vrefp_label = Label(self, text="VREFP", width=15)
        self.vrefp_label.grid(sticky=W, row=56,column=columnbase+2, columnspan=1)
        self.vrefp_val = Label(self, text="",bd=1,relief=SUNKEN,width=10)
        self.vrefp_val.grid(sticky=W, row=56,column=columnbase+3)
        self.vrefp_reg = Label(self, text="",bd=1,relief=SUNKEN,width=15)
        self.vrefp_reg.grid(sticky=W, row=56,column=columnbase+4)

        self.vrefn_label = Label(self, text="VREFN", width=15)
        self.vrefn_label.grid(sticky=W, row=57,column=columnbase+2, columnspan=1)
        self.vrefn_val = Label(self, text="",bd=1,relief=SUNKEN,width=10)
        self.vrefn_val.grid(sticky=W, row=57,column=columnbase+3)
        self.vrefn_reg = Label(self, text="",bd=1,relief=SUNKEN,width=15)
        self.vrefn_reg.grid(sticky=W, row=57,column=columnbase+4)

        self.vcmo_label = Label(self, text="VCMO", width=15)
        self.vcmo_label.grid(sticky=W, row=58,column=columnbase+2, columnspan=1)
        self.vcmo_val = Label(self, text="",bd=1,relief=SUNKEN,width=10)
        self.vcmo_val.grid(sticky=W, row=58,column=columnbase+3)
        self.vcmo_reg = Label(self, text="",bd=1,relief=SUNKEN,width=15)
        self.vcmo_reg.grid(sticky=W, row=58,column=columnbase+4)

        self.vcmi_label = Label(self, text="VCMI", width=15)
        self.vcmi_label.grid(sticky=W, row=59,column=columnbase+2, columnspan=1)
        self.vcmi_val = Label(self, text="",bd=1,relief=SUNKEN,width=10)
        self.vcmi_val.grid(sticky=W, row=59,column=columnbase+3)
        self.vcmi_reg = Label(self, text="",bd=1,relief=SUNKEN,width=15)
        self.vcmi_reg.grid(sticky=W, row=59,column=columnbase+4)

        self.vdda_val=IntVar(self)
        self.vdda_label = Label(self, text="Ext VDDA", width=15)
        self.vdda_label.grid(row=61,column=columnbase+2, columnspan=2)
        self.vddaon_button = Radiobutton(self, text="On", variable = self.vdda_val, value = 1, command=self.vdda_val.get(), width=10)
        self.vddaon_button.grid(sticky=W,row=62,column=columnbase+3)
        self.vddaoff_button = Radiobutton(self, text="Off", variable = self.vdda_val, value = 2, command=self.vdda_val.get(), width=10)
        self.vddaoff_button.grid(sticky=W, row=62,column=columnbase+4)
        self.setvdda_button = Button(self, text="VDDA ON/OFF", command=self.vdda_onoff, width=10)
        self.setvdda_button.grid(row=62,column=columnbase+2,columnspan=1)

        self.readanpow_button = Button(self, text="VDDA Power", command=self.read_anpow, width=10)
        self.readanpow_button.grid(row=63,column=columnbase+2,columnspan=1)
        self.anpow_label = Label(self, text="",bd=1,relief=SUNKEN,width=10)
        self.anpow_label.grid(sticky=W, row=63,column=columnbase+3)

#######  Equipment parameter settings
        self.sec3_label = Label(self,text="Equipment Setup",width=15, height=3)
        self.sec3_label.grid(row=1,column=columnbase+5, columnspan=3)

        self.genampl_label = Label(self,text="Function Generator:",width=20)
        self.genampl_label.grid(row=2,column=columnbase+5, columnspan=3)

        self.genampl_label = Label(self,text="Gen Amplitude:",width=15)
        self.genampl_label.grid(sticky=W,row=3,column=columnbase+5)
        self.genampl_entry = Entry(self,width=15)
        self.genampl_entry.grid(sticky=W,row=3,column=columnbase+6)
        self.ampluni_label = Label(self,text="V",width=3)
        self.ampluni_label.grid(sticky=W,row=3,column=columnbase+7)

        self.genoffs_label = Label(self,text="Gen Offset:",width=15)
        self.genoffs_label.grid(sticky=W,row=4,column=columnbase+5)
        self.genoffs_entry = Entry(self,width=15)
        self.genoffs_entry.grid(sticky=W,row=4,column=columnbase+6)
        self.offsuni_label = Label(self,text="V",width=3)
        self.offsuni_label.grid(sticky=W,row=4,column=columnbase+7)

        self.genfreq_label = Label(self,text="Gen Frequency:",width=15)
        self.genfreq_label.grid(sticky=W,row=5,column=columnbase+5)
        self.genfreq_entry = Entry(self,width=15)
        self.genfreq_entry.grid(sticky=W,row=5,column=columnbase+6)
        self.frequni_label = Label(self,text="Hz",width=3)
        self.frequni_label.grid(sticky=W,row=5,column=columnbase+7)

        self.genset_button = Button(self, text="Generator Setup", command=self.set_generator, width=15)
        self.genset_button.grid(row=50,column=columnbase+5)

        self.genonoff_button = Button(self, text="Generator On/Off", command=self.gen_onoff, width=15)
        self.genonoff_button.grid(row=51,column=columnbase+5,columnspan=1)
        self.genstat_label = Label(self, text="State:",bd=1,relief=SUNKEN,width=15)
        self.genstat_label.grid(sticky=W, row=51,column=columnbase+6)


        self.genampl_label = Label(self,text="Ext VDDA Voltage:",width=20)
        self.genampl_label.grid(sticky=W,row=61,column=columnbase+5, columnspan=3)

        self.vddaampl_label = Label(self,text="PS Voltage:",width=15)
        self.vddaampl_label.grid(sticky=W,row=62,column=columnbase+5)
        self.vddaampl_entry = Entry(self,width=15)
        self.vddaampl_entry.grid(sticky=W,row=62,column=columnbase+6)
        self.vddauni_label = Label(self,text="V",width=3)
        self.vddauni_label.grid(sticky=W,row=62,column=columnbase+7)
        self.vdda_button = Button(self, text="Set VDDA Voltage", command=self.set_vdda, width=15)
        self.vdda_button.grid(sticky=W,row=63,column=columnbase+5)

        self.read_vdda('v')       
        self.gen_state()


    def get_options(self):
        operator = self.operator_entry.get()
        boardid = self.boardid_entry.get()
#        current = None
#        if getCurrent:
#            current = self.current_entry.get()
        # ASIC IDs
        asic_ids = []
        for i in range(0,1):
            serial = self.asic_entries[i].get()
            asic_ids.append(serial)

        variables = [operator,boardid]+asic_ids
        for var in variables:
            if var == "" :
                return
#        if getCurrent:
#            if current == "":
#                return
#            try:
#                current = float(current)
#            except:
#                return

        print("Operator Name: '{}'".format(operator))
        print("Test Board ID: '{}'".format(boardid))
        for i in range(0,1):
            print("ASIC {} ID: '{}'".format(i,asic_ids[i]))

        # need serialnumber list, operator, board_id, timestamp, hostname
        timestamp = self.timestamp
        if timestamp is None:
            timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(":","").replace("-","")
        self.timestamp = timestamp
        hostname = socket.gethostname() 
        chipidstr = ""
        for i in asic_ids:
            chipidstr += str(i) + ","
        chipidstr = chipidstr[:-1]
        runid = "{} {} chip: {}".format(hostname,timestamp, chipidstr)
        print("runid: '{}'".format(runid))

    def reset(self):

 #       if not GUITESTMODE:
#            self.config.POWERSUPPLYINTER.off()
        self.timestamp = None
        for i in reversed(range(len(self.display_procs))):
            tmp = self.display_procs.pop(i)
            tmp.terminate()
            try:
                tmp.wait(2)
            except subprocess.TimeoutExpired:
                tmp.kill()
            del tmp
        for i in reversed(range(len(self.result_labels))):
            tmp = self.result_labels.pop(i)
            tmp.destroy()
        self.status_label["text"] = "NOT STARTED"
        self.status_label["fg"] = "#000000"
        self.status_label["bg"] = self.bkg_color
#        self.runid_label["text"] = ""
        self.prepare_button["state"] = "normal"
#        self.start_button["state"] = "normal"
        self.operator_label["state"] = "normal"
        self.operator_entry["state"] = "normal"
        self.boardid_label["state"] = "normal"
        self.boardid_entry["state"] = "normal"
        self.readtest_button["state"] = "normal"
        self.chantest_button["state"] = "normal"
        self.ch16test_button["state"] = "normal"
        self.noistest_button["state"] = "normal"
        self.linrtest_button["state"] = "normal"
        self.readreg_button["state"] = "normal"
        #self.qctest_button["state"] = "normal"
        self.setvdda_button["state"] = "normal"
        self.regcom_button["state"] = "normal"
        self.resettest_button["state"] = "normal"
        self.readcal_button["state"] = "normal"
        self.measrefv_button["state"] = "normal"
        self.adjrefv_button["state"] = "normal"
#        self.current_label["state"] = "normal"
#        self.current_entry["state"] = "normal"
#        self.current_entry.delete(0,END)
#        self.current_entry["state"] = "normal"
        #self.operator_entry.delete(0,END)
        #self.boardid_entry.delete(0,END)
        #print(self.asic_labels)
        #print(asic_entries)
        for i in range(0,1):
            self.asic_labels[i]["state"] = "normal"
            self.asic_entries[i]["state"] = "normal"
            self.asic_entries[i].delete(0,END)
        self.reset_button["state"] = "normal"    
        self.reset_button["bg"] ="#FF9900"
        self.reset_button["activebackground"] ="#FFCF87"

    def exit(self,*args, **kargs):
#        if not GUITESTMODE:
#            self.config.POWERSUPPLYINTER.off()
        for i in reversed(range(len(self.display_procs))):
            tmp = self.display_procs.pop(i)
            tmp.terminate()
            try:
                tmp.wait(4)
            except subprocess.TimeoutExpired:
                tmp.kill()
            del tmp
        self.destroy()
        self.master.destroy()

def main():
#    from ...configuration.argument_parser import ArgumentParser

    parser = argparse.ArgumentParser(description="ADC test GUI")
    parser.add_argument("-q","--forceQuick",help="Force to run only the ADC offset current off setting (normally runs all when warm)",action="store_true")
    parser.add_argument("-l","--forceLong",help="Force to run over all ADC offset current settings (normally doesn't when cold)",action="store_true")
    args = parser.parse_args()

    root = Tk()
    root.title("ColdADC Test GUI")
    window = GUI_WINDOW(root,forceLong=args.forceLong,forceQuick=args.forceQuick)
    root.mainloop()

if __name__ == '__main__':

    main()

