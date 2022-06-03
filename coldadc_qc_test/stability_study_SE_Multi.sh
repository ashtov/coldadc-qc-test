#!/bin/bash

# WARNING: 
# THIS SCRIPT IS NOW CONFIGURED FOR READING 2 Channels 

ADC0Ch=0
ADC1Ch=0
ADC1ChShift=$((ADC1Ch+8))
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

    # SE -> Free SHA configuration
    cd /home/dune/ColdADC/scripts_cjslin/
    ./writeCtrlReg.py 0 0x63
    ./writeCtrlReg.py 1 0
    ./writeCtrlReg.py 4 0x3b
    ./writeCtrlReg.py 9 0b1000

    # Autocalibration
    ./writeCtrlReg.py 31 0x1
    sleep 2s
    ./writeCtrlReg.py 31 0
    sleep 2s
    ./writeCtrlReg.py 31 0x2
    sleep 2s
    ./writeCtrlReg.py 31 0
    
    #Config=20KHz_SE-SHA
    Config=147KHz_SE-SHA

    #for i in `seq 1 2`; do
    for i in `seq 1 1`; do
	echo "Iteration #${i}"
	cd /home/dune/ColdADC/scripts_cjslin
	#../USB-RS232/turnFuncOFF.py
	#./writeCtrlReg.py 9 0
	#sleep 1s
	#echo "Iteration #${i} calibration"
	#./manualCalib.py

	#../USB-RS232/turnFuncON.py
	#./manualCalib_plots.py
	#sleep 1s
	echo "Iteration #${i} DNL/INL data"

	./plotRamp_2MSamples_Multi.py $ADC0Ch $ADC1ChShift

	python3 calc_linearity_sine.py "temp_2M_${ADC0Ch}.txt"
	mv temp_2M_${ADC0Ch}.txt Sinusoid_${Config}_NomVREFPN_1M_ch${ADC0Ch}_v${i}.txt
	mv temp.png Sinusoid_${Config}_NomVREFPN_ch${ADC0Ch}_v${i}.png

	python3 calc_linearity_sine.py "temp_2M_${ADC1ChShift}.txt"
	mv temp_2M_${ADC1ChShift}.txt Sinusoid_${Config}_NomVREFPN_1M_ch${ADC1ChShift}_v${i}.txt
	mv temp.png Sinusoid_${Config}_NomVREFPN_ch${ADC1ChShift}_v${i}.png

	echo "Iteration #${i} completed"
    done
done

