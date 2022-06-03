
import pandas as pd
import socket
import os
import os.path
import pwd
import sys
import numpy as np
from qc_dnl_inl import calc_dnl_inl
import readADC_NSamp_new
import qc_dnl_inl_new
import glob



start_num=int(input("Input Chip number where to start"))
end_num=int(input("Input Chip number where to end"))
loca_num=input("Input location number")
Test_bid=input("Input test board ID")
NWORDFIFO=65536
DNLSamples=480
file_Diff=[]

for chip_num in range (int(start_num),int(end_num)+1):
    
    file_Diff.append(glob.glob(os.path.dirname("/home/dune/ColdADC/test_results/coldadc_"+Test_bid+"_"+loca_num+"-"+str(chip_num)+"_rt_*"+"/rawLinDataDiff.csv")))
    

for lis in file_Diff:
    for folder in lis:
        print(folder)
        file_exists_Diff=os.path.exists(folder+"/rawLinDataDiff.csv")
        file_exists_SE=os.path.exists(folder+"/rawLinDataSE.csv")
        if file_exists_Diff and file_exists_SE:
            dirsave=folder
            rawLinDataDiff=pd.read_csv(folder+"/rawLinDataDiff.csv")
            begin = folder.index("-")
            end = folder.index("_rt_")
            filename=str(Test_bid+"_"+loca_num+"-"+str(folder[begin+1:end])+"_rt")
            deserLinDataDiff = []
            deserLinDataSE = []
        
        

            for i in range(len(rawLinDataDiff)):
                arr=rawLinDataDiff[rawLinDataDiff.columns[2]][i]
                arr_new=list(arr.split(", "))
                arr_new[0]=arr_new[0][1:]
                arr_new[NWORDFIFO-1]=arr_new[NWORDFIFO-1][:-1]
                firstBlock=np.array(arr_new[0:NWORDFIFO])
                firstBlock=firstBlock.astype(int)
                
            #Deserialize ADC data
                deserLinDataDiff.append (readADC_NSamp_new.deSerialize(firstBlock) )
                if (i%10) == 0:
                    print("Deserialize Sample # ",i)
            del rawLinDataDiff

            qc_dnl_inl_new.calc_dnl_inl(dirsave, filename+'_DIFF', DNLSamples, deserLinDataDiff)
            del deserLinDataDiff
            rawLinDataSE=pd.read_csv(folder+"/rawLinDataSE.csv")
            for i in range(len(rawLinDataSE)):
                arr=rawLinDataSE[rawLinDataSE.columns[2]][i]
                arr_new=list(arr.split(", "))
                arr_new[0]=arr_new[0][1:]
                arr_new[NWORDFIFO-1]=arr_new[NWORDFIFO-1][:-1]
                firstBlock=np.array(arr_new[0:NWORDFIFO])
                firstBlock=firstBlock.astype(int)
            #Deserialize ADC data
                deserLinDataSE.append (readADC_NSamp_new.deSerialize(firstBlock) )
                if (i%10) == 0:
                    print("Deserialize Sample # ",i)
            del rawLinDataSE

            qc_dnl_inl_new.calc_dnl_inl(dirsave, filename+'_SE', DNLSamples, deserLinDataSE)
            del deserLinDataSE
