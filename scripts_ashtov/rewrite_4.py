import numpy as np
import pandas as pd

# copied from dnl_inl_plots.old

def calc_linearity(Codes16):
    '''calc_linearity(Codes16) -> (code, dnl, inlNorm, midADCmean, midADCstd
    Calculates linearity for an array of 16-bit codes Codes16
    Returns code (array), dnl (array), inlNorm (array), midADCmean (float), midADCstd (float)
    Somewhat copied from qc_linearity_sine_14bit.py'''
    Codes14 = Codes16 // 4
    sortCodes14 = np.sort(Codes14)
    print("Codes14.size(): ", np.size(Codes14))
    minbin = sortCodes14[30]
    maxbin = sortCodes14[-30]
    #yoffset = ((sortCodes14[1] + sortCodes14[-2]) / 2) - 8192
    yoffset = ((sortCodes14[1] + sortCodes14[-2]) // 2) - 8192
    minCodes16 = np.amin(Codes16)
    maxCodes16 = np.amax(Codes16)
    minCodes14 = np.amin(Codes14)
    maxCodes14 = np.amax(Codes14)
    print("Min/max code, spread (16bit)=", minCodes16, maxCodes16, maxCodes16 - minCodes16)
    print("Min/max code, spread (14bit)=", minCodes14, maxCodes14, maxCodes14 - minCodes14)
    print("Second Min/max code, offset (14bit)=", sortCodes14[1], sortCodes14[-2], yoffset)
    del sortCodes14

    bins = np.append(np.insert(np.arange(minbin, maxbin + 2) - 0.5, 0, 0.0), 16384.5)
    print("bins: ", bins)
    print("bins.size(): ", np.size(bins))

    h, binedges = np.histogram(Codes14, bins)
    print("h: ", h)
    print("h.size(): ", np.size(h))
    midADCmean = np.mean(h[7500:8200])
    midADCstd = np.std(h[7500:8200])
    print('midADCmean: ', midADCmean)
    print('midADCstd: ', midADCstd)
    ch = np.cumsum(h)
    histosum = np.sum(h)
    end = np.size(ch)
    T = -np.cos(np.pi * ch / histosum)
    hlin = np.subtract(T[1:end], T[0:end - 1])

    TRUNC = 30
    hlin_size = np.size(hlin)
    hlin_trunc = hlin[TRUNC:hlin_size - TRUNC]
    lsb = np.average(hlin_trunc)
    dnl = np.insert(hlin_trunc / lsb - 1, 0, 0.0)
    inl = np.cumsum(dnl)
    inlNorm = inl - np.mean(inl)
    #code = np.linspace(minbin + TRUNC, maxbin - TRUNC, np.size(dnl)).astype(int)    # should be arange maybe???
    #code = np.arange(minbin + TRUNC, maxbin - TRUNC + 1)
    code = np.linspace(minbin + TRUNC, maxbin - TRUNC, np.size(dnl)).astype(np.uint16)

    return code, dnl, inlNorm, midADCmean, midADCstd
    #return code

subprocess.run(['./deserialize', 'rawLinDataDiff.bin', 'LinDataDiff_deserialized.bin'])
c = np.fromfile('LinDataDiff_deserialized.bin', dtype=np.uint16)
print(c)
#d = c.reshape(16, 983040, order='F').T
d = c.reshape(983040, 16)
print(d)
print(list(d[0][:20]))
#y = pd.DataFrame(d)
#print(y)
#code, dnl, inlNorm, midADCmean, midADCstd  = np.apply_along_axis(calc_linearity, 0, d)
#code = np.apply_along_axis(calc_linearity, 0, d)
#print(code)
#print(dnl)
#print(inlNorm)
#print(midADCmean)
#print(midADCstd)

COLUMNS = ['code', 'dnl', 'inlNorm', 'midADCmean', 'midADCstd']

data = pd.DataFrame(d).apply(calc_linearity).T.rename_axis('Channel').astype({3: 'float64', 4: 'float64'})
data.columns = COLUMNS
print(data)
print(data.dtypes)
print(data.at[0, 'code'])

print('Calculating dnlstd . . .')
data['dnlstd'] = data.loc[slice(None), 'dnl'].map(np.std)
print('Calculating maxinl . . .')
data['maxinl'] = data.loc[slice(None), 'inlNorm'].map(np.max)
print('Calculating mininl . . .')
data['mininl'] = data.loc[slice(None), 'inlNorm'].map(np.min)

print(data)
print(data.dtypes)
print(data.at[0, 'code'])
