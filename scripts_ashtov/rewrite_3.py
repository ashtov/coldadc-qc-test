import numpy as np
import pandas as pd
import subprocess
import glob

FILENAMES = glob.glob('coldadc_enr_3-273_3_rt*/rawLinData*.csv')
print(FILENAMES)

for fname in FILENAMES:
    if fname[-5] == 'f':
        mode = 'DIFF'
    else:
        mode = 'SE'
    a = pd.read_csv(fname, quoting=3, skiprows=1, header=None, converters={2: lambda x: np.uint8(x[2:]), 65537: lambda x: np.uint8(x[:-2])}).loc[slice(None), 2:].astype('uint8')
    print(a)
    print(a.dtypes)
    b = np.array(a)
    print(b)
    b.tofile('rawLinDataDiff.bin', sep='')
    subprocess.run(['./deserialize', 'rawLinDataDiff.bin', 'LinDataDiff_deserialized.bin'])
    c = np.fromfile('LinDataDiff_deserialized.bin', dtype=np.uint16)
    print(c)
    d = np.insert(c.reshape(983040, 16), 0, np.arange(0, 983040), axis=1)
    print(d)
    for i in range(3):
        print(list(d[i]))
    #np.savetxt(f'coldadc_enr_3-271_ln_20220531T121503/ColdADC_enr_3-271_ln_{mode}_dnl_inl.csv', d, fmt='%d',  delimiter=',')
    np.savetxt(fname[:fname.rfind('/')] + f'/ColdADC_enr_3-273_3_rt_{mode}_dnl_inl.csv', d, fmt='%d', delimiter=',')
