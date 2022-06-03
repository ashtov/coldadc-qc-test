#!/bin/bash
#source /home/dune/venv/bin/activate
cd /home/dune/ColdADC/scripts_cjslin/enableCMOS_p2/
./coldADC_ldo_off.py
sleep 0.1
cd ..
./coldADC_resetADC.py
sleep 0.1
./coldADC_resetFPGA.py
sleep 0.1
cd enableCMOS_p2/
./coldADC_ldo_on.py
sleep 0.1
cd ..
./coldADC_resetADC.py 
sleep 0.1
cd enableCMOS_p2/
./coldADC_enableCMOS_NomRef_CMO1p20.sh 
sleep 0.1
cd ..
./writeCtrlReg.py 0 0x63
sleep 0.1
./writeCtrlReg.py 1 0
sleep 0.1
./writeCtrlReg.py 4 0x3b
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
cd /home/dune/ColdADC/
