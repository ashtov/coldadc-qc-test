import matplotlib.pyplot as plot
import numpy as np
import csv

if __name__ == "__main__":
    vals = [[] for i in range(16)]
#    with open('ColdADC__dnl_inl.csv') as csvfile:
    with open('ColdADC_2041_00045_ln_DIFF_dnl_inl.csv') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            for i in range(1,17):
                vals[i-1].append(row[i].strip())
    for i in range(1,17):
        with open("gui_ch%d.txt" % i, 'w') as out:
            for j in range(len(vals[i-1])):
                out.write(vals[i-1][j] + '\n')    
