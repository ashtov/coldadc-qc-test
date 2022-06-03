# Values set for room temperature for ColdADC P2

# Enable CMOS reference and single-ended-to differential
#./coldADC_writeCtrlReg.py 0 0b01100010

## For packaged P2 #0046; LDO VDDA=2.25V
#./coldADC_writeCtrlReg.py 24 0xe3
#./coldADC_writeCtrlReg.py 25 0x30
#./coldADC_writeCtrlReg.py 26 0x8a
#./coldADC_writeCtrlReg.py 27 0x66

## For packaged P2 #0044; LDO VDDA=2.25V
./coldADC_writeCtrlReg.py 24 0xdc
./coldADC_writeCtrlReg.py 25 0x2f
./coldADC_writeCtrlReg.py 26 0x85
./coldADC_writeCtrlReg.py 27 0x63




