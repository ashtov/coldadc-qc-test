import glob
import numpy as np
from matplotlib import pyplot as plt
from find_chipID import find_chipID

filenames = {}
filenames['rt'] = glob.glob('../test_results/coldadc_enr_3-*_rt*/test_report*.txt')
filenames['ln'] = glob.glob('../test_results/coldadc_enr_3-*_ln*/test_report*.txt')

filenames['rt_23'] = []
filenames['rt_25'] = []
for i in filenames['rt']:
    if int(find_chipID(i)[2:]) < 91:
        filenames['rt_23'].append(i)
    else:
        filenames['rt_25'].append(i)

VOLTAGES = ['24', '25', '26', '27']
REGNAMES = ['VREFP', 'VREFN', 'VCMO', 'VCMI']

settings = {'rt_23': {}, 'rt_25': {}, 'ln': {}}

TEMPS = ['rt_23', 'rt_25', 'ln']

for temp in TEMPS:
    for filename in filenames[temp]:
        chipID = find_chipID(filename)
        print(chipID)
        with open(filename, 'r') as f:
            while f.readline().lstrip()[:8] != 'Register':
                pass
            settings[temp][chipID] = {}
            for regnum in VOLTAGES:
                l = [i.strip() for i in f.readline().split(',')]
                if l[0] != regnum:
                    print(filename)
                    raise ValueError("faulty input")
                settings[temp][chipID][regnum] = int(l[1], base=16)
#print(settings)
f, ax = plt.subplots(4, 1, constrained_layout=True)
f.set_size_inches(8, 20)
#f.suptitle('Reference Voltage Register Settings')
for i in range(4):
    ax[i].set_title(REGNAMES[i])
    x = ([], [], [])
    for j in range(3):
        for chipID, v in settings[TEMPS[j]].items():
            x[j].append(v[VOLTAGES[i]])
    bins = np.arange(min((min(x[0]), min(x[1]), min(x[2]))), max((max(x[0]), max(x[1]), max(x[2]))) + 2)
    print(f'bins: {bins}')
    ax[i].hist(x, bins=bins, align='left', histtype='barstacked')
    ax[i].set_xticks(bins[:-1])
    ax[i].set_xticklabels([hex(k) for k in bins[:-1]], fontsize=7)
    #ax[i].set_xlabel(f'{REGNAMES[i]} value')
    ax[i].set_ylabel('# of chips')
f.legend(['RT ChipID < 3-90', 'RT ChipID > 3-90', 'Liquid Nitrogen'], fontsize=18)
f.savefig('refvoltage_register_settings.png')

'''
len1 = 0
#[len1 += 1 for chipID in settings if int(chipID[2:]) < 91]
for chipID in settings:
    if int(chipID[2:]) < 91:
        len1 += 1
len2 = len(settings) - len1
print(len1)
print(len2)
print(len(settings))
for regnum in VOLTAGES:
    f, ax = plt.subplots(1, 1)
    ax.set_title(f'Reference Voltage Register Settings ({temp}): {REGNAMES[regnum]}')
    f.set_size_inches(15, 10)
    x1 = np.empty(len1, dtype=np.int16)
    x2 = np.empty(len2, dtype=np.int16)
    count1 = 0
    count2 = 0
    for chipID, v in settings.items():
        if int(chipID[2:]) < 91:
            x1[count1] = v[regnum]
            count1 += 1
        else:
            x2[count2] = v[regnum]
            count2 += 1
    #nbins = abs(np.max(x) - np.min(x)) + 1
    bins = np.arange(min((np.min(x1), np.min(x2))), max((np.max(x1), np.max(x2))) + 2)
    print(f'bins: {bins}')
    ax.hist((x1, x2), bins=bins, align='left', histtype='barstacked')
    ax.set_xticks(bins[:-1])
    ax.set_xticklabels([hex(i) for i in bins[:-1]])
    ax.set_xlabel(f'{REGNAMES[regnum]} value')
    ax.set_ylabel('# of chips')
    ax.legend(['ChipID < 3-90', 'ChipID > 3-90'], fontsize=18)
    f.savefig(f'refvoltage_register_settings_{temp}_{REGNAMES[regnum]}.png')
'''
