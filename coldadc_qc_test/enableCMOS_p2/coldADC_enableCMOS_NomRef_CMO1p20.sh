# Values set for room temperature for ColdADC P2

# Enable CMOS reference and single-ended-to differential
#./coldADC_writeCtrlReg.py 0 0b01100010


## FOR VDDA=2.323V RT (dropped to 2.300V at LN2); nominal CMOS references
#./coldADC_writeCtrlReg.py 24 0xdc
#./coldADC_writeCtrlReg.py 25 0x2f
#./coldADC_writeCtrlReg.py 26 0x85
#./coldADC_writeCtrlReg.py 27 0x62

## FOR VDDA2P5=2.25V ; nominal CMOS references
#./coldADC_writeCtrlReg.py 24 0xe2
#./coldADC_writeCtrlReg.py 25 0x30
#./coldADC_writeCtrlReg.py 26 0x89
#./coldADC_writeCtrlReg.py 27 0x66

## For bare die ASIC#4 ? VDDA2P5=2.25V
#./coldADC_writeCtrlReg.py 24 0xdc
#./coldADC_writeCtrlReg.py 25 0x2f
#./coldADC_writeCtrlReg.py 26 0x85
#./coldADC_writeCtrlReg.py 27 0x62

## For bare die ColdADC_P2 ASIC#1 ? VDDA2P5=2.50V (external power supply)
./coldADC_writeCtrlReg.py 24 0xce
./coldADC_writeCtrlReg.py 25 0x2c
./coldADC_writeCtrlReg.py 26 0x7d
./coldADC_writeCtrlReg.py 27 0x5c


# Nominal CMOS refernce bias current adjust 
#./coldADC_writeCtrlReg.py 23 0x20

# Using CMOS with internal R
# Trim setting 101 --> ~50uA of current
#./coldADC_writeCtrlReg.py 28 0b10101

# Setting ADC bias current to ~50uA
#./coldADC_writeCtrlReg.py 8 0b1011

# Reset FPGA
#./coldADC_resetFPGA.py


