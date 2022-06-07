# Values set for LN2 temperature for ColdADC P2 ASIC

# Enable CMOS reference and single-ended-to differential
#./coldADC_writeCtrlReg.py 0 0b01100010


## Internal LDO with VDDA=2.25V
## nominal CMOS references
./coldADC_writeCtrlReg.py 24 0xdf
./coldADC_writeCtrlReg.py 25 0x33
./coldADC_writeCtrlReg.py 26 0x89
./coldADC_writeCtrlReg.py 27 0x67

## External power supply  with VDDA=2.5V
## nominal CMOS references
#./coldADC_writeCtrlReg.py 24 0xca
#./coldADC_writeCtrlReg.py 25 0x2e
#./coldADC_writeCtrlReg.py 26 0x7e
#./coldADC_writeCtrlReg.py 27 0x60


## FOR Board # 4 EXTERNAL (BK Precision) VDDA=2.28V
## nominal CMOS references
#./coldADC_writeCtrlReg.py 24 0xdd
#./coldADC_writeCtrlReg.py 25 0x32
#./coldADC_writeCtrlReg.py 26 0x88
#./coldADC_writeCtrlReg.py 27 0x66



