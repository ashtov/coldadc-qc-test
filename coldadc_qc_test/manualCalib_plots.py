#!/usr/bin/env python3

import time
import binascii
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from scipy.optimize import curve_fit
from scipy.stats import norm
import numpy as np
import matplotlib.backends.backend_pdf

        

def main(fileName):
    inFile=open(fileName,"r")
    
    #Number of words in FPGA FIFO
    NWORDFIFO=65536

    stage0Hist=[]; stage0Hist.append([]); stage0Hist.append([]);
    stage0Hist.append([]); stage0Hist.append([]);
    stage1Hist=[]; stage1Hist.append([]); stage1Hist.append([]);
    stage1Hist.append([]); stage1Hist.append([]);
    stage2Hist=[]; stage2Hist.append([]); stage2Hist.append([]);
    stage2Hist.append([]); stage2Hist.append([]);
    stage3Hist=[]; stage3Hist.append([]); stage3Hist.append([]);
    stage3Hist.append([]); stage3Hist.append([]);
    stage4Hist=[]; stage4Hist.append([]); stage4Hist.append([]);
    stage4Hist.append([]); stage4Hist.append([]);
    stage5Hist=[]; stage5Hist.append([]); stage5Hist.append([]);
    stage5Hist.append([]); stage5Hist.append([]);
    stage6Hist=[]; stage6Hist.append([]); stage6Hist.append([]);
    stage6Hist.append([]); stage6Hist.append([]);

    
    nCount=0
    stageNum=-1; nData=-1
    for iLine in inFile:
        if nCount==0:
            texts=iLine.split(",")
            stageNum=int(texts[0])
            nData=int(texts[1])
            print("Stage # and number of data =",stageNum, nData)
        else:
            if stageNum==0:
                stage0Hist[int((nCount-1)/nData)].append(int(iLine))
            if stageNum==1:
                stage1Hist[int((nCount-1)/nData)].append(int(iLine))
            if stageNum==2:
                stage2Hist[int((nCount-1)/nData)].append(int(iLine))
            if stageNum==3:
                stage3Hist[int((nCount-1)/nData)].append(int(iLine))
            if stageNum==4:
                stage4Hist[int((nCount-1)/nData)].append(int(iLine))
            if stageNum==5:
                stage5Hist[int((nCount-1)/nData)].append(int(iLine))
            if stageNum==6:
                stage6Hist[int((nCount-1)/nData)].append(int(iLine))

        nCount += 1
        
        if (nCount > (nData*4)):
            nCount=0

    ###############################
    #  Plot Stage 0 weights
    ###############################
    fig0 = plt.figure()
        
    ax1 = fig0.add_subplot(2,2,1)
    plt.ylabel('Counts')
    plt.title('Stage 0')
    plt.gcf().text(0.20,0.8,"S0")
    plt.hist(stage0Hist[0][:],log=False,bins=19, align='mid')    
    
    ax2 = fig0.add_subplot(2,2,2)
    plt.title('Stage 0')
    plt.gcf().text(0.60,0.8,"S1")
    plt.hist(stage0Hist[1][:],log=False,bins=19, align='mid')

    ax3 = fig0.add_subplot(2,2,3)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.20,0.4,"S2")
    plt.ylabel('Counts')
    plt.hist(stage0Hist[2][:],log=False,bins=19, align='mid')    

    ax4 = fig0.add_subplot(2,2,4)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.60,0.4,"S3")
    plt.hist(stage0Hist[3][:],log=False,bins=19, align='mid')    
    

    ###############################
    #  Plot Stage 1 weights
    ###############################

    fig1 = plt.figure()
        
    ax1 = fig1.add_subplot(2,2,1)
    plt.ylabel('Counts')
    plt.title('Stage 1')
    plt.gcf().text(0.20,0.8,"S0")
    plt.hist(stage1Hist[0][:],log=False,bins=13, align='mid')    
    
    ax2 = fig1.add_subplot(2,2,2)
    plt.title('Stage 1')
    plt.gcf().text(0.60,0.8,"S1")
    plt.hist(stage1Hist[1][:],log=False,bins=13, align='mid')

    ax3 = fig1.add_subplot(2,2,3)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.20,0.4,"S2")
    plt.ylabel('Counts')
    plt.hist(stage1Hist[2][:],log=False,bins=13, align='mid')    

    ax4 = fig1.add_subplot(2,2,4)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.60,0.4,"S3")
    plt.hist(stage1Hist[3][:],log=False,bins=13, align='mid')    

    ###############################
    #  Plot Stage 2 weights
    ###############################

    fig2 = plt.figure()
        
    ax1 = fig2.add_subplot(2,2,1)
    plt.ylabel('Counts')
    plt.title('Stage 2')
    plt.gcf().text(0.20,0.8,"S0")
    plt.hist(stage2Hist[0][:],log=False,bins=9, align='mid')    
    
    ax2 = fig2.add_subplot(2,2,2)
    plt.title('Stage 2')
    plt.gcf().text(0.60,0.8,"S1")
    plt.hist(stage2Hist[1][:],log=False,bins=9, align='mid')

    ax3 = fig2.add_subplot(2,2,3)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.20,0.4,"S2")
    plt.ylabel('Counts')
    plt.hist(stage2Hist[2][:],log=False,bins=9, align='mid')    

    ax4 = fig2.add_subplot(2,2,4)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.60,0.4,"S3")
    plt.hist(stage2Hist[3][:],log=False,bins=9, align='mid')    

    ###############################
    #  Plot Stage 3 weights
    ###############################

    fig3 = plt.figure()
        
    ax1 = fig3.add_subplot(2,2,1)
    plt.ylabel('Counts')
    plt.title('Stage 3')
    plt.gcf().text(0.20,0.8,"S0")
    plt.hist(stage3Hist[0][:],log=False,bins=5, align='mid')    
    
    ax2 = fig3.add_subplot(2,2,2)
    plt.title('Stage 3')
    plt.gcf().text(0.60,0.8,"S1")
    plt.hist(stage3Hist[1][:],log=False,bins=5, align='mid')

    ax3 = fig3.add_subplot(2,2,3)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.20,0.4,"S2")
    plt.ylabel('Counts')
    plt.hist(stage3Hist[2][:],log=False,bins=5, align='mid')    

    ax4 = fig3.add_subplot(2,2,4)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.60,0.4,"S3")
    plt.hist(stage3Hist[3][:],log=False,bins=5, align='mid')    


    ###############################
    #  Plot Stage 4 weights
    ###############################

    fig4 = plt.figure()
        
    ax1 = fig4.add_subplot(2,2,1)
    plt.ylabel('Counts')
    plt.title('Stage 4')
    plt.gcf().text(0.20,0.8,"S0")
    plt.hist(stage4Hist[0][:],log=False,bins=3, align='mid')    
    
    ax2 = fig4.add_subplot(2,2,2)
    plt.title('Stage 4')
    plt.gcf().text(0.60,0.8,"S1")
    plt.hist(stage4Hist[1][:],log=False,bins=3, align='mid')

    ax3 = fig4.add_subplot(2,2,3)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.20,0.4,"S2")
    plt.ylabel('Counts')
    plt.hist(stage4Hist[2][:],log=False,bins=3, align='mid')    

    ax4 = fig4.add_subplot(2,2,4)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.60,0.4,"S3")
    plt.hist(stage4Hist[3][:],log=False,bins=3, align='mid')    


    ###############################
    #  Plot Stage 5 weights
    ###############################

    fig5 = plt.figure()
        
    ax1 = fig5.add_subplot(2,2,1)
    plt.ylabel('Counts')
    plt.title('Stage 5')
    plt.gcf().text(0.20,0.8,"S0")
    plt.hist(stage5Hist[0][:],log=False,bins=2, align='mid')    
    
    ax2 = fig5.add_subplot(2,2,2)
    plt.title('Stage 5')
    plt.gcf().text(0.60,0.8,"S1")
    plt.hist(stage5Hist[1][:],log=False,bins=2, align='mid')

    ax3 = fig5.add_subplot(2,2,3)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.20,0.4,"S2")
    plt.ylabel('Counts')
    plt.hist(stage5Hist[2][:],log=False,bins=2, align='mid')    

    ax4 = fig5.add_subplot(2,2,4)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.60,0.4,"S3")
    plt.hist(stage5Hist[3][:],log=False,bins=2, align='mid')    

    ###############################
    #  Plot Stage 6 weights
    ###############################

    fig6 = plt.figure()
        
    ax1 = fig6.add_subplot(2,2,1)
    plt.ylabel('Counts')
    plt.title('Stage 6')
    plt.gcf().text(0.20,0.8,"S0")
    plt.hist(stage6Hist[0][:],log=False,bins=2, align='mid')    
    
    ax2 = fig6.add_subplot(2,2,2)
    plt.title('Stage 6')
    plt.gcf().text(0.60,0.8,"S1")
    plt.hist(stage6Hist[1][:],log=False,bins=2, align='mid')

    ax3 = fig6.add_subplot(2,2,3)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.20,0.4,"S2")
    plt.ylabel('Counts')
    plt.hist(stage6Hist[2][:],log=False,bins=2, align='mid')    

    ax4 = fig6.add_subplot(2,2,4)
    plt.xlabel('ADC Channel')
    plt.gcf().text(0.60,0.4,"S3")
    plt.hist(stage6Hist[3][:],log=False,bins=2, align='mid')    

    #plt.show()

    pdf = matplotlib.backends.backend_pdf.PdfPages("temp_S0-3.pdf")
    #for fig in range(1, figure().number): ## will open an empty extra figure :(
    pdf.savefig( fig0 )
    pdf.savefig( fig1 )
    pdf.savefig( fig2 )
    pdf.savefig( fig3 )
    pdf.savefig( fig4 )
    pdf.savefig( fig5 )
    pdf.savefig( fig6 )
    pdf.close()

    
    #Close output file
    inFile.close()

if __name__ == '__main__':

    fileName="temp_calibData.txt"
    if (len(sys.argv) > 1):
        fileName=sys.argv[1]

    main(fileName)
