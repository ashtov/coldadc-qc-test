# All-in-one FPGA I/O class
# Should help keep everything more organised
# ashtov 2022-06-08

import time
import spidev
import RPi.GPIO as GPIO
import numpy as np

class FPGA:
    FPGA_FIFO_FULL = 12
    UART_SEL=27
    FPGA_RESET=22
    ADC_RESET=6
    VREFFMON_EN=5 
    LDO_VDDA = 24
    LDO_VDDD = 13

    def __init__(self):
        '''FPGA() --> FPGA
        Initialize FPGA controller.'''
        self.SPI = spidev.SpiDev()
        self.SPI.open(0, 0)
        self.SPI.max_speed_hz = 8000000
        self.SPI.mode = 0b01
        GPIO.setmode(GPIO.BCM)
        #GPIO.setwarnings(False)
        GPIO.setup((self.FPGA_FIFO_FULL, self.UART_SEL, self.FPGA_RESET, self.ADC_RESET, self.VREFFMON_EN, self.LDO_VDDA, self.LDO_VDDD),
                    (GPIO.IN, GPIO.OUT, GPIO.OUT, GPIO.OUT, GPIO.OUT, GPIO.OUT, GPIO.OUT))
        GPIO.output((self.UART_SEL, self.FPGA_RESET, self.ADC_RESET, self.VREFFMON_EN, self.LDO_VDDA, self.LDO_VDDD),
                    (GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.LOW))
        self.gport = GPIO

    def cleanup(self):
        '''FPGA.cleanup() closes ports'''
        self.SPI.
        self.gport.cleanup()

    def reset_FPGA(self):
        '''Resets FPGA (0.5 s)'''
        self.gport.output(self.FPGA_RESET, GPIO.LOW)
        time.sleep(0.5)
        self.gport.output(self.FPGA_RESET, GPIO.HIGH)

    def reset_FPGA(self):
        '''Resets ADC (0.5 s)'''
        self.gport.output(self.ADC_RESET, GPIO.LOW)
        time.sleep(0.5)
        self.gport.output(self.ADC_RESET, GPIO.HIGH)

    def ldo_VDDA_on(self):
        '''Enables LDO VDDA'''
        self.gport.output(self.LDO_VDDA, GPIO.HIGH)

    def ldo_VDDA_off(self):
        '''Disables LDO VDDA'''
        self.gport.output(self.LDO_VDDA, GPIO.LOW)

    def ldo_VDDD_on(self):
        '''Enables LDO VDDD'''
        self.gport.output(self.LDO_VDDD, GPIO.HIGH)

    def ldo_VDDD_off(self):
        '''Disables LDO VDDD'''
        self.gport.output(self.LDO_VDDD, GPIO.LOW)

    def ldo_on(self):
        '''Turns on LDO'''
        self.ldo_VDDA_on()
        self.ldo_VDDD_on()

    def ldo_off(self):
        '''Turns off LDO'''
        self.ldo_VDDA_off()
        self.ldo_VDDD_off()

    def sel_UART(self):
        '''Selects UART mode'''
        self.gport.output(self.UART_SEL, GPIO.HIGH)

    def sel_i2c(self):
        '''Selects I2C mode'''
        self.gport.output(self.UART_SEL, GPIO.LOW)

    def pollFIFO(self):
        '''Polls FIFO, returns when done'''
        while self.gport.input(self.FPGA_FIFO_FULL) == GPIO.LOW:
            time.sleep(0.01)
