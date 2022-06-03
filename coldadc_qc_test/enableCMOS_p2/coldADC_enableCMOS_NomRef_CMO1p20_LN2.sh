# Values set for LN2 temperature for ColdADC P2 ASIC

# Enable CMOS reference and single-ended-to differential
#./coldADC_writeCtrlReg.py 0 0b01100010

## FOR Board # 4 EXTERNAL (BK Precision) VDDA=2.53V
## nominal CMOS references
#./coldADC_writeCtrlReg.py 24 0xc7
#./coldADC_writeCtrlReg.py 25 0x2d
#./coldADC_writeCtrlReg.py 26 0x7b
#./coldADC_writeCtrlReg.py 27 0x5c

## FOR Board # 4 with LDO at VDDA=2.300V
## nominal CMOS references
./coldADC_writeCtrlReg.py 24 0xda
./coldADC_writeCtrlReg.py 25 0x32
./coldADC_writeCtrlReg.py 26 0x86
./coldADC_writeCtrlReg.py 27 0x64

## FOR Board # 4 EXTERNAL (BK Precision) VDDA=2.28V
## nominal CMOS references
#./coldADC_writeCtrlReg.py 24 0xdd
#./coldADC_writeCtrlReg.py 25 0x32
#./coldADC_writeCtrlReg.py 26 0x88
#./coldADC_writeCtrlReg.py 27 0x66

## FOR Board # 4 with LDO at VDDA=2.19V
## nominal CMOS references
#./coldADC_writeCtrlReg.py 24 0xe5
#./coldADC_writeCtrlReg.py 25 0x34
#./coldADC_writeCtrlReg.py 26 0x8d
#./coldADC_writeCtrlReg.py 27 0x69

# Reset FPGA
#./coldADC_resetFPGA.py


