import glob
import numpy as np
from matplotlib import pyplot as plt

folders = glob.glob("coldadc_enr_3-*/test_report*.txt")

print(folders)

VOLTAGES = ['24', '25', '26', '27']
voltages = {}

for filename in folders:
    index = filename.find('enr_') + 4
    chipID = filename[index:filename.find('_', index)]
    print(chipID)
    with open(filename, 'r') as f:
        while f.readline().lstrip()[:8] != 'Register':
            pass
        voltages[chipID] = {}
        for vname in VOLTAGES:
            l = [i.strip() for i in f.readline().split(',')]
            print(l)
            if l[0] != vname:
                print(filename)
                raise ValueError("faulty input")
            voltages[chipID][vname] = float(l[2])
print(voltages)

for vname in VOLTAGES:
    f, ax = plt.subplots(1, 1)
    ax.set_title(f'Reference Voltage Settings: {vname}')
    f.set_size_inches(15,10)
    x = []
    for k, v in voltages.items():
        x.append(v[vname])
        if (vname == '24' and v[vname] < 1.9) or (vname == '25' and v[vname] > 0.46):
            print(f'Outlier: for register {vname}, chip {k}')
    #x = [i[vname] for i in voltages.values()]
    nbins = (max(x) - min(x)) / 0.001
    print(nbins)
    ax.hist(x, bins=int(nbins))
    f.savefig(f'ref_voltages_{vname}.png')
