import numpy as np
import pandas as pd
import subprocess

a = pd.read_csv('rawLinDataDiff.csv', quoting=3, skiprows=1, header=None, converters={2: lambda x: np.uint8(x[2:]), 65537: lambda x: np.uint8(x[:-2])}).loc[slice(None), 2:].astype('uint8')
print(a)
print(a.dtypes)
b = np.array(a)
print(b)
b.tofile('rawLinDataDiff.bin', sep='')
subprocess.run(['./deserialize', 'rawLinDataDiff.bin', 'LinDataDiff_deserialized.bin'])
c = np.fromfile('LinDataDiff_deserialized.bin', dtype=np.uint16)
print(c)
d = c.reshape(983040, 16)
print(d)
for i in range(3):
    print(list(d[i]))
np.savetxt('DiffLinearity.csv', d, fmt='%d',  delimiter=',')
