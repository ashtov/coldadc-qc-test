#!/bin/bash
#source /home/dune/venv/bin/activate
cd /home/dune/ColdADC/coldadc_qc_test/enableCMOS_p2/
./coldADC_ldo_off.py
sleep 3.0
cd ..
./coldADC_resetADC.py
sleep 1.0
./coldADC_resetFPGA.py
sleep 1.0
cd enableCMOS_p2/
./coldADC_ldo_on.py
sleep 1.0
cd ..
./coldADC_resetADC.py 
sleep 1.0
cd enableCMOS_p2/
./coldADC_enableCMOS_NomRef_CMO1p20.sh 
sleep 1.0
cd ..
./writeCtrlReg.py 0 0xa3
sleep 0.1
./writeCtrlReg.py 1 0
sleep 0.1
./writeCtrlReg.py 4 0x33
sleep 0.1
./writeCtrlReg.py 9 0b1000
sleep 0.1
./writeCtrlReg.py 31 0x1
sleep 0.1
./writeCtrlReg.py 31 0
sleep 0.1
./writeCtrlReg.py 31 0x2
sleep 0.1
./writeCtrlReg.py 31 0
sleep 0.1
./writeCtrlReg.py 41 1
