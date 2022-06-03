#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time

#Default GPIO settings on powerup (need to verify this)
#GPIO 0-8 pull0ups to 3.3V; GPIO 9-27 pull-downs to 0V


GPIO.setmode(GPIO.BCM)
#GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#Define GPIO pins
FPGA_FIFO_FULL=26
UART_SEL=27
FPGA_RESET=22
ADC_RESET=6

#Set input and output pins
GPIO.setup(FPGA_FIFO_FULL, GPIO.IN)
GPIO.setup(UART_SEL, GPIO.OUT)
GPIO.setup(FPGA_RESET, GPIO.OUT)

#Set output pin initial state
GPIO.output(UART_SEL, GPIO.HIGH)
GPIO.output(FPGA_RESET, GPIO.HIGH)
time.sleep(0.5)

#Reset FPGA
GPIO.output(FPGA_RESET, GPIO.LOW)
time.sleep(0.5)
GPIO.output(FPGA_RESET, GPIO.HIGH)

#Exit GPIO cleanly
GPIO.cleanup
