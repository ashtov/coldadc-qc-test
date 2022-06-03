""" Functions to perform frequency domain analysis of ADC output codes
    Updated 9/20/2020 to fixed normalization, added ENOB correction - CRG
    
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
        
def AnalyzeDynamicADC(Codes,N=4096,NumBits=12,SamplingRate=1, window = None):
    """ 
    Analyses ADC output codes to calculate 12-bit performance parameters.
    Inputs :
        Codes -- List of ADC input codes. Expects 16-bit positive integer codes
            (offset binary) 
        N -- length of FFT (should be power of two)
        NumBits -- Number of bits in ADC
        SamplingRate -- can be provided to scale to frequency axis if desired
                    must be in MHz
        window -- an array of N, or None if no windowing
    Outputs:
        SNDR -- signal-to-noise plus distortion ratio
        ENOB -- Effective Number of Bits (based on SNDR)
        SNR -- signal-to-noise ratio (distortion removed)
        SFDR -- Spurious-Free Dynamic Range (ratio of input tone
                                             and biggest spur)
        THD -- Total Harmonic Distortion (ratio of input tone to sum of 
                                          next 10 harmonics)
    
    The code takes the first N samples of the input list and normalizes. 
    After taking the FFT is calculates the various performance metrics and 
    returns.
    Author: Carl Grace (crgrace@lbl.gov)
    """

    MinValue = 1e-6 # close to noise floor    
    # first convert from 16-bit to N-bit words
    CodeArray = np.array(Codes[0:N])   # create numpy array
    CodeRange = max(CodeArray) - min(CodeArray) # how many codes used?

#    print(CodeRange)
    CodeArray = CodeArray/2**NumBits #normalize
    if window is not None:
        CodeArray *= window 
    
    X = np.abs(np.fft.fft(CodeArray)/(N))
    X = X[0:int(N/2)] # drop redundant half
#    print('Full Scale = ',max(X))
    IdealFullScale= 0.104949008462 # fron ideal ADC test
    X_db = 20*np.log10(np.abs(X)) # want to plot in log scale
    X_db = 20*np.log10(np.abs(X)/max(np.abs(X))) # want to plot in log scale
    
    X_db = 20*np.log10(np.abs(X)/IdealFullScale) # want to plot in log scale
    X_db[0] = -99
    # calculate SNDR
    # SNDR is (input tone power) / (sum of all other bins)
    X_sndr = np.copy(X) # make copy for calculations
    X_sndr[0] = MinValue
    if window is not None:
        X_sndr[1:10] = MinValue # need this when windowing
        X_db[0:5] = -95
    InputBin = np.argmax(X_sndr)  # where is the input tone?

    leakage_bins =  5
    if window is not None:
#        leakage_bins =  5
        InputBins = np.arange(max(0,InputBin-leakage_bins),InputBin+leakage_bins+1)
        leakage_power = np.sum(X_sndr[InputBins]**2)
        InputPower = 10*np.log10(leakage_power)
        NoiseAndDistPower = 10*np.log10(np.sum(X_sndr**2)-leakage_power)
        X_sndr[InputBins] = MinValue
    else:
        InputBins = InputBin
        InputPower = 20*np.log10(X_sndr[InputBin])
        NoiseAndDistPower = 10*np.log10(np.sum(X_sndr**2) - X_sndr[InputBin]**2)
        X_sndr[InputBin] = MinValue
    SNDR = InputPower - NoiseAndDistPower

    # calculate ENOB
    ENOB = (SNDR - 1.76 + 20*np.log10(2**NumBits/CodeRange)) / 6.02

    #calculate SFDR
    # SFDR is difference between input tone and highest spur
    PeakSpurBin = np.argmax(X_sndr)    
    SFDR = InputPower - 20*np.log10(X_sndr[PeakSpurBin])
    
    # calculate SNR & THD
    # THD is measure of distortion in data without considering noise
    # SNR is signal-to-noise ignoring distortion (harmonics of input tone)
    # first get location of harmonics
    NumHarms = 5 
    AliasedHarms = FindAliasedHarmonics(N,InputBin,NumHarms)
    # Harmonics also have spectral leakage (they are spread over a few bins) 
    # so care must be taken here. The approach is to find the harmonics and
    # replace their energy with the average noise floor 
    for CurrentHarm in AliasedHarms:       
        if (CurrentHarm != InputBin):  # ignore fundamental harmonic
            HarmBins = np.arange(max(0,CurrentHarm-leakage_bins),CurrentHarm+leakage_bins+1)
            for Bin in HarmBins:
                X_sndr[Bin] = MinValue;

    leakage_power = np.sum(X_sndr[InputBins]**2)       
    NoisePower = 10*np.log10(np.sum(X_sndr**2) - np.sum(X_sndr[InputBins]**2))        

    SNR = InputPower - NoisePower
    THD = 10*np.log10(10**(-SNDR/10)-10**(-SNR/10))
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
    plt.text(xFraction*max(Freqs),max(X_db)-10,'N = %d' %(N), fontsize = FontSize)
    plt.text(xFraction*max(Freqs),max(X_db)-20,
         'SNDR = %.2f dB' %(SNDR), fontsize = FontSize)
    plt.text(xFraction*max(Freqs),max(X_db)-30,
         'ENOB = %.2f bits' %(ENOB), fontsize = FontSize)
    plt.text(xFraction*max(Freqs),max(X_db)-40,
         'SNR = %.2f dB' %(SNR), fontsize = FontSize)
    plt.text(xFraction*max(Freqs),max(X_db)-50,
         'SFDR = %.2f dB' %(SFDR), fontsize = FontSize)
    plt.text(xFraction*max(Freqs),max(X_db)-60,
         'THD = %.2f dB' %(THD), fontsize = FontSize)
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
    return SNDR, ENOB, SNR, SFDR, THD, Freqs, X_db
   


def AnalyzeDynamicADCTest(NumBits=12):
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
    NumCodes = 2**NumBits
    Ts = 1.0/Fs; # sampling interval
    Fin = (Fs*Cycles)/NumSamples;   # frequency of the signal
    LSB = 2/(2**NumBits)

    
    y = []  # build up test signal
    for i in range(0,NumSamples):
        Sample = math.sin(2*math.pi*Fin*i*Ts)
        Sample = (math.floor(Sample/LSB)*LSB)*NumCodes/2
        y.append(Sample)
    
    window = np.blackman(NumSamples)
    SNDR, ENOB, SNR, SFDR, THD, plt = AnalyzeDynamicADC(y,NumSamples,NumBits,Fs,window)
    ExpectedResults = [74.006,12.001,92.092,-1080.34]
    # check results
    if (NumBits == 12):
        Failed = 0
        if ((SNDR > 74.1) or (SNDR < 73.7)):
            Failed = 1
        if ((ENOB > 12.1) or (ENOB < 11.0)):
            Failed = 1
        if ((SFDR > 94.1) or (SFDR < 91.9)):
            Failed = 1
        if ((THD > -90) or (THD < -100)):
            Failed = 1    
        if (Failed):
            print('AnalyzeDynamicADC FAILED test')
            print('returned: SNDR, ENOB, SFDR, THD = ',SNDR,ENOB,SFDR,THD )
            print('expected: SNDR, ENOB, SFDR, THD = ',ExpectedResults)
        else:
            print('AnalyzeDynamicADC passed test')
    else:
        print('AnalyzeDynamicADCTest: Results only checked at 12 bits')
        

if __name__=="__main__":        

    # test functions
    #FindAliasedHarmonicsTest()
    #AnalyzeDynamicADCTest(12)        

    #Codes16 = np.loadtxt("../Data/LN2_147kHz_NoClkSync_09-11-2020/Sinusoid_147KHz_SE-SHA_NomVREFPN_1M_ch0_v1.txt")
    #Codes16 = np.loadtxt("../Data/Sinusoid_147KHz_Diff_autoCal_VCMO0x72_NomVREFPN_1M_ch2_v1.txt")
    #Codes16 = np.loadtxt("../Data/Sinusoid_147KHz_Diff_SHA_NomVREFPN_ch4_v1.txt")
    Codes16 = np.loadtxt("LN2_PKG1_Diff_NomVREFPN_12-16-2020/Sinusoid_147KHz_Diff_NomVREFPN_1M_ch0_v1.txt")

    Codes12 = []
    Codes14 = []

    # downsample from 16-bits to 14- or 12-bits
    for CurrentCode in Codes16[0:2048]:
    #        Codes14.append(int(np.floor(CurrentCode)/4))
        Codes12.append(int(np.floor(CurrentCode)/16))

    #window = np.kaiser(2048,12)        
    window = np.hanning(2048)        
    #window = None
    #window = np.blackman(2048)       

    AnalyzeDynamicADC(Codes12,2048,12,2,window)
    #plt.title('147KHz_Diff_autoCal_VCMO0x72_NomVREFPN_1M_ch2_v1')
    #plt.title('Sinusoid_147KHz_Diff_SHA_NomVREFPN_ch4_v1')
    plt.title('Sinusoid_147KHz_ADC-Test_NomVREFPN_ch0_v1')

    #plt.title('Ideal 12-bit ADC')
    #plt.savefig('v2_fft_script_ideal12b.png',format='png',dpi=300)
    plt.savefig('Sinusoid_147KHz_ADC-Test_NomVREFPN_ch0_v1.png',format='png',dpi=300)
    #plt.savefig('Sinusoid_147KHz_Diff_SHA_NomVREFPN_ch4_v1',format='png',dpi=300)
