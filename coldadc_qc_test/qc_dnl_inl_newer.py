# Completely rewritten qc_dnl_inl_new.py, now taking 1.3 seconds rather than
# 38 minutes.
# Use with deserialize.c and version of gui_new.py with same date.
# By ashtov 2022-06-01


import os
import subprocess
import time
#import binascii
#import sys
#import serial
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO
import spidev
#import writeCtrlReg
#import readCtrlReg
#from test_equipment.srs_ds360 import SRS_DS360

def calc_linearity(Codes16):
    '''calc_linearity(Codes16) -> (code, dnl, inlNorm, midADCmean, midADCstd
    Calculates linearity for an array of 16-bit codes Codes16
    Returns code (array), dnl (array), inlNorm (array), midADCmean (float), midADCstd (float)
    Somewhat copied from qc_linearity_sine_14bit.py'''
    Codes14 = Codes16 // 4
    sortCodes14 = np.sort(Codes14)
    minbin = sortCodes14[30]
    maxbin = sortCodes14[-30]
    #yoffset = ((sortCodes14[1] + sortCodes14[-2]) / 2) - 8192
    yoffset = ((sortCodes14[1] + sortCodes14[-2]) // 2) - 8192
    minCodes16 = np.amin(Codes16)
    maxCodes16 = np.amax(Codes16)
    minCodes14 = np.amin(Codes14)
    maxCodes14 = np.amax(Codes14)
    print("Min/max code, spread (16bit)=", minCodes16, maxCodes16, maxCodes16 - minCodes16)
    print("Min/max code, spread (14bit)=", minCodes14, maxCodes14, maxCodes14 - minCodes14)
    print("Second Min/max code, offset (14bit)=", sortCodes14[1], sortCodes14[-2], yoffset)
    del sortCodes14

    bins = np.append(np.insert(np.arange(minbin, maxbin + 2) - 0.5, 0, 0.0), 16384.5)

    h, binedges = np.histogram(Codes14, bins)
    midADCmean = np.mean(h[7500:8200])
    midADCstd = np.std(h[7500:8200])
    print('midADCmean: ', midADCmean)
    print('midADCstd: ', midADCstd)
    ch = np.cumsum(h)
    histosum = np.sum(h)
    end = np.size(ch)
    T = -np.cos(np.pi * ch / histosum)
    hlin = np.subtract(T[1:end], T[0:end - 1])

    TRUNC = 30
    hlin_size = np.size(hlin)
    hlin_trunc = hlin[TRUNC:hlin_size - TRUNC]
    lsb = np.average(hlin_trunc)
    dnl = np.insert(hlin_trunc / lsb - 1, 0, 0.0)
    inl = np.cumsum(dnl)
    inlNorm = inl - np.mean(inl)
    #code = np.linspace(minbin + TRUNC, maxbin - TRUNC, np.size(dnl)).astype(int)    # should be arange maybe???
    #code = np.arange(minbin + TRUNC, maxbin - TRUNC + 1)
    code = np.linspace(minbin + TRUNC, maxbin - TRUNC, np.size(dnl)).astype(np.uint16)
    print(f"Range of code: {minbin + TRUNC} - {maxbin - TRUNC}, difference: {maxbin - TRUNC - (minbin + TRUNC)}\nSize of 'code': {np.size(code)}")

    #return {'code': code, 'dnl': dnl, 'inlNorm': inlNorm, 'midADCmean': midADCmean, 'midADCstd': midADCstd}
    #return pd.Series([code, dnl, inlNorm, midADCmean, midADCstd])
    return code, dnl, inlNorm, midADCmean, midADCstd


def calc_plot_dnl_inl(indata, dirsave=None, asicID='', NumSet=480):
    '''indata should be array of uint8
    Calculates and plots DNL and INL, and saves a bunch of figures, given raw
    linearity data
    '''
    if dirsave == None:
        dirsave = os.environ.get("PWD")
        print(dirsave)

    # DO NOT CHANGE THESE NUMBERS
    # (without changing the numbers in 'deserialize')
    NChan = 16
    NWORDFIFO = 65536

    ADC0Num = 7     # necessary?
    ReadMode = 2    # necessary?
    SampRate = 1. / 2E6
    NTimeStp = 983040   # NWORDFIFO // 32 * NumSet

    print('Writing raw data to temp file . . .')
    indata.tofile('rawLinData.bin', sep='')
    subprocess.run(['./deserialize', 'rawLinData.bin', 'LinData.bin', str(NumSet)])
    print('Reading deserialized data . . .')
    # array formatted for further processing
    y = np.fromfile('LinData.bin', dtype=np.uint16).reshape(NTimeStp, NChan)
    # DEBUG
    print(y)
    #y = temp.reshape(NChan, NTimeStp, order='F')        # array formatted for further processing
    print('Saving linearity data to CSV . . .')
    y_csv = np.insert(y, 0, np.arange(0, NTimeStp), axis=1)
    np.savetxt(f'{dirsave}/ColdADC_{asicID}_dnl_inl.csv', y_csv, fmt='%u', delimiter=',')
    del y_csv
    print(f'Saved linearity data to {dirsave}/ColdADC_{asicID}_dnl_inl.csv')

    COLUMNS = ['code', 'dnl', 'inlNorm', 'midADCmean', 'midADCstd']
    #data = pd.DataFrame(y)
    #print(data)
    #data = data.T.apply(calc_linearity, raw=True, axis=1, result_type='expand')
    #print(data)
    #data.columns = COLUMNS
    #data.astype({'midADCmean': np.float64, 'midADCstd': np.float64}, copy=False)
    #print(data)
    data = pd.DataFrame(y).apply(calc_linearity).T.astype({3: 'float64', \
            4: 'float64'}).rename_axis('Channel')
    data.columns = COLUMNS
    print(data)
    data['max_dnl'] = data.loc[slice(None), 'dnl'].map(np.max)
    data['min_dnl'] = data.loc[slice(None), 'dnl'].map(np.min)
    print('Calculating dnlstd . . .')
    data['std_dnl'] = data.loc[slice(None), 'dnl'].map(np.std)
    print('Calculating maxinl . . .')
    data['max_inl'] = data.loc[slice(None), 'inlNorm'].map(np.max)
    print('Calculating mininl . . .')
    data['min_inl'] = data.loc[slice(None), 'inlNorm'].map(np.min)

    dnl_inl_report = data.loc[slice(None), 'max_dnl':'min_inl']
    dnl_inl_report.to_csv(f'{dirsave}/ColdADC_{asicID}_dnl_inl_report.csv')

    SUPTITLES = [
            'DNL for All ADC0 Channels',
            'DNL for All ADC1 Channels',
            'INL for All ADC0 Channels',
            'INL for All ADC1 Channels'
            ]
    OUTFSUF = [
            'DNL_ADC0',
            'DNL_ADC1',
            'INL_ADC0',
            'INL_ADC1'
            ]
    YLABELS = [
            'DNL [LBS]',
            'DNL [LBS]',
            'INL [LBS]',
            'INL [LBS]'
            ]
    DATAPOINTS = ['dnl', 'dnl', 'inlNorm', 'inlNorm']
    figs, axes = tuple(zip(*[plt.subplots(4, 2) for i in range(4)]))   # magic
    for i in range(4):
        figs[i].suptitle(SUPTITLES[i])
        figs[i].set_size_inches(15, 15)
        for ch in range(NChan // 2):
            col = ch // 4
            row = ch - col * 4
            if col == 0:
                axes[i][row, col].set_ylabel(YLABELS[i])
            if row == 0:
                axes[i][row, col].set_title(f'Channel {ch + 1}')
            elif row == 3:
                axes[i][row, col].set_xlabel('ADC Code')
            truech = ch + 8 if i % 2 else ch
            axes[i][row, col].plot(data.at[truech, 'code'], data.at[truech, DATAPOINTS[i]])
        figs[i].savefig(f'{dirsave}/ColdADC_{asicID}_{OUTFSUF[i]}.png')
    f, ax = plt.subplots()
    ax.set_ylim((0, 50))
    ax.set_xlabel('Channel')
    ax.set_ylabel('Mid Occupancy StD [ADC]')
    ax.plot(np.arange(0, NChan), data.loc[slice(None), 'midADCstd'], '.')
    f.savefig(f'{dirsave}/ColdADC_{asicID}_Occup_StD.png')
    #print('test12')
    plt.show(block=False)
    #print('test10')
    #f.clear()
    #[i.clear() for i in figs]
    #plt.close('all')
    #print('test11')
    return data


# I don't know what these do, but they're necessary
# copied from readADC_NSamp_new.py (to make that file unnecessary)

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
    FPGA_FIFO_FULL=12           # LOL what does this do???

    #Set input and output pins
    GPIO.setup(fpgaFull, GPIO.IN)
    return GPIO


# modified to be smaller
def pollFIFO(GPort,FIFO_FULL):
    #Poll FPGA Fifo state
    while GPort.input(FIFO_FULL) != 1:
        pass


def readNSamp(GPort,SPI,FIFO,NWORD,NSamples):
    print('Reading data from ADC . . .')
    pollFIFO(GPort,FIFO)
    dummy=SPI.readbytes(NWORD)
    dataSample = np.empty((NSamples, NWORD), dtype=np.uint8)
    t0 = time.time()
    for i in range(NSamples):
        pollFIFO(GPort,FIFO)

        ##########################################################################
        #Reading out ColdADC FIFO data
        ##########################################################################
#        adcDataBlock=SPI.readbytes(NWORD)
        dataSample[i] = np.array(SPI.readbytes(NWORD), dtype=np.uint8)
    t1 = time.time()
    print("time to read: ", t1-t0)
    return dataSample
