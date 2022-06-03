#!/bin/bash

# WARNING: 
# THIS SCRIPT IS NOW CONFIGURED FOR READING ONE DIFFERENTIAL CHANNEL FULL CHAIN

ADC0Ch=-1
ADC1Ch=3

#Set AllChannel to 1 if reading out all 16 channels
AllChannel=1

if [[ $ADC0Ch -eq -1 ]]
then
	ADCCh=$((ADC1Ch+8))
	ADC0Ch=0
else
	ADCCh=$ADC0Ch
	ADC1Ch=0
fi
FrozenSHAWord=$(((ADC1Ch<<5)+(ADC0Ch<<2)+3))

cd /home/dune/ColdADC/USB-RS232
#./freq20.5078KHz.py


for j in 1p20; do

    #################################
    cd /home/dune/ColdADC/scripts_cjslin/
    #./coldADC_resetADC.py
    #./coldADC_resetFPGA.py
    cd /home/dune/ColdADC/USB-RS232
    ./setAmplitudeVolt.py 1.4

    #################################

    # Differential input (bypass DB) -> Free SHA configuration
    cd /home/dune/ColdADC/scripts_cjslin/
    ./writeCtrlReg.py 0 0xa3
    ./writeCtrlReg.py 1 0
    ./writeCtrlReg.py 4 0x33 # Nominal SHA current

    # Single-ended input (bypass SDC) -> Free SHA configuration
    #./writeCtrlReg.py 0 0x63
    #./writeCtrlReg.py 1 0
    #./writeCtrlReg.py 4 0x3b

    ## Set binary offset
    ./writeCtrlReg.py 9 0b1000
    ## Set binary offset and ADC_Test mode
    #./writeCtrlReg.py 9 0b101000

    #Shift VCMI (LN2; VDDA2P5=2.19V)
    #./writeCtrlReg.py 27 0x59   # VCMI=0.80
    #./writeCtrlReg.py 27 0x5f   # VCMI=0.85
    #./writeCtrlReg.py 27 0x64   # VCMI=0.90
    #./writeCtrlReg.py 27 0x6a   # VCMI=0.95
    #./writeCtrlReg.py 27 0x6f   # VCMI=1.00
    #./writeCtrlReg.py 27 0x75   # VCMI=1.05
    
    
    #Shift VMCO (LN2; VDDA2P5=2.19V)
    #echo "Shifting VCMO voltage"
    #./writeCtrlReg.py 26 0x8d   # 1.2 V at LN2
    #./writeCtrlReg.py 26 0x87   # 1.15 V at LN2
    #./writeCtrlReg.py 26 0x81   # 1.1 V at LN2
    #./writeCtrlReg.py 26 0x7e   # 1.08V at LN2
    #./writeCtrlReg.py 26 0x75   # 1.0V at LN2

    #Shift VMCO (RT, VDDA2P5=2.26V)
    #echo "Shifting VCMO voltage"
    #./writeCtrlReg.py 26 0x89   # 1.2V at RT
    #./writeCtrlReg.py 26 0x83   # 1.15V at RT
    #./writeCtrlReg.py 26 0x7d   # 1.1 V at RT
    #./writeCtrlReg.py 26 0x71   # 1.0 V a RT

    #Tarun's settings to increase RefBuf current to 600uA
    #./writeCtrlReg.py 4 0x66  #Reduce SHA current by half
    #./writeCtrlReg.py 5 0x66  #Reduce SHA current by half
    #./writeCtrlReg.py 6 0x66  #Reduce SHA current by half
    #./writeCtrlReg.py 7 0x66  #Reduce SHA current by half
    #./writeCtrlReg.py 8 0x0e  #Reduce ADC current by half
    #./writeCtrlReg.py 23 0x0f  #Increase REF BIAS to MAX
    #./writeCtrlReg.py 28 0x09  #Double master bias current
    
    
    # Autocalibration
    #./writeCtrlReg.py 41 1
    #./writeCtrlReg.py 9 0

    ./writeCtrlReg.py 31 0x1
    #sleep 2s
    ./writeCtrlReg.py 31 0
    #sleep 2s
    ./writeCtrlReg.py 31 0x2
    #sleep 2s
    ./writeCtrlReg.py 31 0
    ./writeCtrlReg.py 41 1
    #./writeCtrlReg.py 9 0b101000   #ADC Test
    
    # not sure if this is the right config...
    #Config=20KHz_DBypass-SHA
    #Config=147KHz_Diff_SHA_vcmo0x75
    #Config=147KHz_Diff_autoCal_VCMO0x72_OverFlowOFF
    Config=LN2_147KHz_Diff
    #Config=147KHz_ADC-Test
    #Config=147KHz_ADC-Test_VCMO0x83

    RefConfig=NomVREFPN
    #RefConfig=NomVREFPN-VinVCMI0p90
    #RefConfig=VREFPN-200mV

    startCh=$ADCCh
    endCh=$ADCCh+1
    if [[ $AllChannel -eq 1 ]]
    then
       startCh=0
       endCh=16
    fi


    for i in `seq 1 1`; do
    #for i in `seq 2 20`; do
	echo "Iteration #${i}"
	cd /home/dune/ColdADC/scripts_cjslin
	#../USB-RS232/turnFuncOFF.py
	#./writeCtrlReg.py 9 0
	#sleep 1s
	#echo "Iteration #${i} calibration"
	#./manualCalib.py
	
	#../USB-RS232/turnFuncON.py
	#./manualCalib_plots.py
	sleep 1s
	echo "Iteration #${i} DNL/INL data"
	
	if [[ $AllChannel -eq 0 ]]
	then
	    ./plotRamp_2MSamples_Multi.py $ADCCh
	else
	    ./plotRamp_2MSamples_Multi.py 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
	    #./plotRamp_2MSamples_Multi.py 0 2 4 6 8 10 12 14
	    #./plotRamp_2MSamples_Multi.py 7 15
	fi

	#chList=" 0 2 4 6 8 10 12 14 "
	#for iCh in $chList ; do	    
	for ((iCh = $startCh; iCh < $endCh; iCh++)); do
	    python3 calc_linearity_sine.py "temp_2M_${iCh}.txt"
	    mv temp_2M_${iCh}.txt Sinusoid_${Config}_${RefConfig}_1M_ch${iCh}_v${i}.txt
	    mv temp.png Sinusoid_${Config}_${RefConfig}_ch${iCh}_v${i}.png

	    #./readCalibWeights.py > CalibWts_ch${iCh}_v${i}.txt
	done


	echo "Iteration #${i} completed"
    done
done

