#!/usr/bin/env python3

import subprocess
import numpy as np
import qc_dnl_inl_newer

FPGA_FIFO_FULL = 12
NWORDFIFO = 65536
DNLSamples = 480
dirsave = 'data_order_test'
asicID = '3-277_DIFF'

def get_raw_data(gport, spi):
    samp = qc_dnl_inl_newer.readNSamp(gport, spi, FPGA_FIFO_FULL, NWORDFIFO, 1)
    print('Writing raw data to temp file . . .')
    samp.tofile('rawLinData.bin', sep='')
    subprocess.run(['./data_order_test/deserialize_2', 'rawLinData.bin', 'LinData.bin', '1'])
    print('Reading deserialized data . . .')
    y = np.fromfile('LinData.bin', dtype=np.uint16).reshape(2048, 16)
    print(y)
    print('Saving linearity data to CSV . . .')
    y_csv = np.insert(y, 0, np.arange(0, 2048), axis=1)
    np.savetxt('data_order_test/data.csv', y_csv, fmt='%u', delimiter=',')
    print('Saved linearity data to data_order_test/data.csv')

# this doesn't work, FIFO won't read out more than 65536 bytes
def get_raw_data_double(gport, spi):
    samp = qc_dnl_inl_newer.readNSamp(gport, spi, FPGA_FIFO_FULL, NWORDFIFO * 2, 1)
    print('Writing raw data to temp file . . .')
    samp.tofile('rawLinData.bin', sep='')
    subprocess.run(['./data_order_test/deserialize_2', 'rawLinData.bin', 'LinData.bin', '2'])
    print('Reading deserialized data . . .')
    y = np.fromfile('LinData.bin', dtype=np.uint16).reshape(4096, 16)
    print(y)
    print('Saving linearity data to CSV . . .')
    y_csv = np.insert(y, 0, np.arange(0, 4096), axis=1)
    np.savetxt('data_order_test/data.csv', y_csv, fmt='%u', delimiter=',')
    print('Saved linearity data to data_order_test/data.csv')

def get_serialized_data(gport, spi):
    samp = qc_dnl_inl_newer.readNSamp(gport, spi, FPGA_FIFO_FULL, NWORDFIFO, 1)
    print('Writing raw data to file . . .')
    samp = samp.reshape(16384, 4)
    np.savetxt('data_order_test/serialized_data.csv', samp, fmt='%u', delimiter=',')
    print('Saved serialized data to data_order_test/serialized_data.csv')

if __name__ == '__main__':
    spi = qc_dnl_inl_newer.initSPI()
    gport = qc_dnl_inl_newer.initGPIOpoll(FPGA_FIFO_FULL)
    get_raw_data(gport, spi)
    #get_raw_data_double(gport, spi)
    #get_serialized_data(gport, spi)
    spi.close()
    gport.cleanup()


#rawLinData = qc_dnl_inl_newer.readNSamp(gport, spi, FPGA_FIFO_FULL, NWORDFIFO, DNLSamples)
#qc_dnl_inl_newer.calc_plot_dnl_inl(rawLinData, dirsave, asicID, DNLSamples)
#del rawLinData
