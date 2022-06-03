""" Functions to perform frequency domain analysis of ADC output codes
    These functions require the sampling rate and the input frequency to 
    be "mutually prime". For more info:
    please see "How to Test ADCs" by Carl Grace
"""
import matplotlib.pyplot as plt
import numpy as np
import math
    

def FindAliasedHarmonics(NumBins,FunBin,NumHarms):
    """ 
    Calculates location of aliased harmonics in an FFT record. Any harmonics
    that are above the Nyquist frequency will be aliased back down into the
    first Nyquist zone (we use modulo arithmetic here to make that happen)
    Inputs :
        NumBins -- Number of bins in FFT
        FunBin -- Bin where fundamental tone is located
        NumHarms -- Number of Aliased Harmonics desired
    Outputs:
        HarmBins -- List of bins where harmonics are located
            List starts at 1st harmonic, which is same as fundamental
    Author: Carl Grace (crgrace@lbl.gov)
    """    

    NyquistBin = NumBins/2
    HarmBins = []
    for i in range(1,NumHarms+1):
        CurrentHarmBin = i*FunBin
        if ((int(CurrentHarmBin/NyquistBin) % 2) == 0): # odd nyquist zone
            HarmBins.append(int(CurrentHarmBin % NyquistBin))
        else: # even nyquist zone
            HarmBins.append(int(NyquistBin-(CurrentHarmBin % NyquistBin)))
    return HarmBins

def FindAliasedHarmonicsTest():
    """ Tests FindAliasedHarmonics function
    """
    Numbins = 4096
    FunBin = 534
    NumHarms = 10
    AliasedHarms = FindAliasedHarmonics(Numbins,FunBin,NumHarms)
    AliasedHarmsExpected = [534,1068,1602,1960,1426,892,358,176,710,1244]
    if (AliasedHarms == AliasedHarmsExpected):
        print('FindAliasedHarmonics passed test')
    else:
        print('FindAliasedHarmonics FAILED test')
        print('Returned:',AliasedHarms)
        print('Expected:',AliasedHarmsExpected)
        
def AnalyzeDynamicADC(Codes,N=4096,SamplingRate=1, window = None):
    """ 
    Analyses ADC output codes to calculate performance parameters.
    Inputs :
        Codes -- List of ADC input codes. Expects positive integer codes
            (offset binary)
        N -- length of FFT (should be power of two)
        SamplingRate -- can be provided to scale to frequency axis if desired
                    must be in MHz
        window -- an array of N, or None if no windowing
    Outputs:
        SNDR -- signal-to-noise plus distortion ratio
        ENOB -- Effective Number of Bits
        SFDR -- Spurious-Free Dynamic Range (ratio of input tone
                                             and biggest spur)
        THD -- Total Harmonic Distortion (ratio of input tone to sum of 
                                          next 10 harmonics)
    
    The code takes the first N samples of the input list and normalizes. 
    After taking the FFT is calculates the various performance metrics and 
    returns.
    Author: Carl Grace (crgrace@lbl.gov)
    """
    CodeArray = np.array(Codes)
    if window is not None:
        CodeArray = CodeArray * window 
    CodeArray = (CodeArray-N/2)/N  # normalize array    
    
    X = np.abs(np.fft.fft(CodeArray)/(N/2))
    X = X[0:int(N/2)] # drop redundant half
    X_db = 20*np.log10(np.abs(X)) # want to plot in log scale

    # calculate SNDR
    # SNDR is (input tone power) / (sum of all other bins)
    X_sndr = np.copy(X) # make copy for calculations
    X_sndr[0] = 0.0
    if window is not None:
        X_sndr[1:4] = 0.0 #probably need this when windowing
    InputBin = np.argmax(X_sndr)  # where is the input tone
    if window is not None:
        leakage_bins = 2 
        InputBins = np.arange(max(0,InputBin-leakage_bins),InputBin+leakage_bins+1)
        leakage_power = np.sum(X_sndr[InputBins]**2)
        InputPower = 10*np.log10(leakage_power)
        NoisePower = 10*np.log10(np.sum(X_sndr**2)-leakage_power)
        X_sndr[InputBins] = 0.0
    else:
        InputPower = 20*np.log10(X_sndr[InputBin])
        NoisePower = 10*np.log10(np.sum(X_sndr**2) - X_sndr[InputBin]**2)
        X_sndr[InputBin] = 0.0
    SNDR = InputPower - NoisePower

    # calculate ENOB
    ENOB = (SNDR - 1.76) / 6.02

    #calculate SFDR
    # SFDR is difference between input tone and highest spur
    PeakSpurBin = np.argmax(X_sndr)
    SFDR = InputPower - 20*np.log10(X_sndr[PeakSpurBin])
    
    # calculate THD
    # THD is measure of distortion in data without concern with noise
    # first get location of harmonics
    NumHarms = 10 # use first 10 harmonics
    AliasedHarms = FindAliasedHarmonics(N,InputBin,NumHarms)    
    DistortionPower = 0.0
    for CurrentHarm in AliasedHarms:
        if (CurrentHarm != InputBin):  # ignore fundamental harmonic
            DistortionPower += 20*np.log10(X_sndr[CurrentHarm])
    THD = DistortionPower - InputPower


    #plot results 
    
    Freqs = np.linspace(0,0.5,int(N/2))
    if (SamplingRate != 1): # scaling value provided
        xLabelText = 'Frequency [MHz]'
        Freqs = Freqs * SamplingRate
    else:
        xLabelText = r'Normalized Frequency [$\Omega$]'
    xFraction = 0.5 # how far along x-axis to put text
    FontSize = 10
    if window is not None:
        plt.plot(Freqs[4:Freqs.size],X_db[4:X_db.size]) # no DC component    
    else:
        plt.plot(Freqs[1:Freqs.size],X_db[1:X_db.size]) # no DC component    
    plt.xlabel(xLabelText)
    plt.text(xFraction*max(Freqs),max(X_db)-20,'Bins = %d' %(N), fontsize = FontSize)
    plt.text(xFraction*max(Freqs),max(X_db)-30,
         'SNDR = %.2f dB' %(SNDR), fontsize = FontSize)
    plt.text(xFraction*max(Freqs),max(X_db)-40,
         'ENOB = %.2f bits' %(ENOB), fontsize = FontSize)
    plt.text(xFraction*max(Freqs),max(X_db)-50,
         'SFDR = %.2f dB' %(SFDR), fontsize = FontSize)
    #plt.text(xFraction*max(Freqs),max(X_db)-60,
         #'THD = %.2f dB' %(THD), fontsize = FontSize)
    plt.ylabel('Amplitude [dBFS]')
    """
    fig = plt.figure()
    x0 = np.arange(0, 2048)*1./2E6 
    plt.title("Input codes (after windowing)")
    plt.xlabel("time (s)")
    plt.scatter(x0, CodeArray)

    fig = plt.figure()
    x0 = np.arange(0, 1024)
    plt.title("fft values")
    plt.xlabel("freq (Mhz)")
    plt.scatter(Freqs, X_db)

    plt.show()
    """
    #plt.savefig('adc_dynamic_performace.png',format='png',dpi=300)
    return SNDR, ENOB, SFDR, THD, plt
   


def AnalyzeDynamicADCTest(inputData):
    """ Tests AnalyzeDynamicADC function
    """        

    ## ADC Test Input
    #Fs = 16.0;  # sampling rate
    #Cycles = 151 # number of cycles in record
    #NumSamples = 16384

    ## Single Channel
    Fs = 2.0;  # sampling rate
    Cycles = 21 # number of cycles in record
    NumSamples = 2048
    
    Bits = 16
    NumCodes = 2**Bits
    Ts = 1.0/Fs; # sampling interval
    Fin = (Fs*Cycles)/NumSamples;   # frequency of the signal
    LSB = 2/(2**Bits)

    """
    y = []  # build up test signal
    for i in range(0,NumSamples):
        Sample = math.sin(2*math.pi*Fin*i*Ts)
        Sample = (math.floor(Sample/LSB)*LSB)*NumCodes + NumCodes/2
        y.append(Sample)
    """
    y = inputData
    
    SNDR, ENOB, SFDR, THD = AnalyzeDynamicADC(y,NumSamples,Fs)
    ExpectedResults = [74.006,12.001,92.092,-1080.34]
    # check results
    Failed = 0
    if ((SNDR > 74.1) or (SNDR < 73.9)):
        Failed = 1
    if ((ENOB > 12.1) or (ENOB < 11.0)):
        Failed = 1
    if ((SFDR > 92.1) or (SFDR < 91.9)):
        Failed = 1
    if (THD > -1000):
        Failed = 1
        
    if (Failed):
        print('AnalyzeDynamicADC FAILED test')
        print('returned: SNDR, ENOB, SFDR, THD = ',SNDR,ENOB,SFDR,THD )
        print('expected: SNDR, ENOB, SFDR, THD = ',ExpectedResults)
    else:
        print('AnalyzeDynamicADC passed test')
    
# test functions
#FindAliasedHarmonicsTest()
#AnalyzeDynamicADCTest()


