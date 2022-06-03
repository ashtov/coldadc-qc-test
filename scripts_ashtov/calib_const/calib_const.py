# Calibration constant analysis
# by ashtov 2022-04-18
# modified for better data display 2022-05-19

import glob
import numpy as np
from matplotlib import pyplot as plt

folders = glob.glob("../coldadc_enr_3-*_rt_*/*calib_const.csv")
print(folders)

constants = {}
bad = []
known_bad = ['3-45', '3-66']

for filename in folders:
    index = filename.find('enr_') + 4
    chipID = filename[index:filename.find('_', index)]
    print(chipID)
    if chipID not in known_bad:
        constants[chipID] = []
        with open(filename, 'r') as f:
            for l in f:
                constants[chipID].append([int(i.strip(), base=16) for i in l.split(',')])
                if constants[chipID][-1][3] > 1500:
                    print(f'chipID: {chipID} {constants[chipID][-1]}: [3] is {constants[chipID][-1][3]} > 1500')
                    bad.append(chipID)
                if constants[chipID][-1][5] < -1500:
                    print(f'chipID: {chipID} {constants[chipID][-1]}: [5] is {constants[chipID][-1][5]} < -1500')
                    bad.append(chipID)
#print(constants)

f, ax = plt.subplots(14, 2)
f.set_size_inches(10, 50)

for reg in range(14):
    x = [[], []]
    nbins = [0, 0]
    for k, v in constants.items():
        x[0].append(v[reg][3])
        x[1].append(v[reg][5])
    for i in range(2):
        ax[reg][i].set_title(f'Calibration constants: {reg}, W{i}')
        nbins[i] = (max(x[i]) - min(x[i])) or 1
        print(nbins[i])
        ax[reg][i].hist(x[i], bins=nbins[i])
f.savefig('calib_const.png')
print(f'Bad chips: {bad}')
