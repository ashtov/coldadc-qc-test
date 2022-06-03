#!/bin/bash


for j in 1p20; do

    #################################
    cd /home/dune/ColdADC/scripts/
    #./coldADC_resetADC.py
    #./coldADC_resetFPGA.py

    #################################
    ##### Clap VREFPN by +-100mV
    ####  Looping over VCMO index j
    #cd /home/dune/ColdADC/scripts_cjslin/enableCMOS/
    #./coldADC_enableCMOS_Ref_100mV_CMO${j}_LN2.sh
    #./coldADC_enableCMOS_NomRef_CMO${j}.sh

    # Disable frontend for ADC only
    cd /home/dune/ColdADC/scripts_cjslin/
    ./writeCtrlReg.py 0 0x63


    for i in `seq 1 1`; do
	echo "Iteration #${i}"
	cd /home/dune/ColdADC/scripts_cjslin
	../USB-RS232/turnFuncOFF.py
	./writeCtrlReg.py 9 0
	sleep 1s
	echo "Iteration #${i} calibration"
	./manualCalib.py

	../USB-RS232/turnFuncON.py
	./manualCalib_plots.py
	sleep 1s

	mv temp_calibData.txt CalibData_NomVREFPN_VDDA2p50.txt
	mv temp_S0-3.pdf Calib_S0-3_NomVREFPN_VDDA2p50.pdf
        #./manualCalib_plots.py temp_calibData2.txt
        #mv temp_calibData2.txt CalibData_NomVREFPN_v${i}.txt
        #mv temp_S0-3.pdf Calib_S0-3_NomVREFPN_ADC1_v${i}.pdf
	./readCalibWeights.py > CalibWts_NomVREFPN_VDDA2p50.txt
	echo "Iteration #${i} completed"
    done
done
