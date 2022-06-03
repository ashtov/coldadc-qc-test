import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob
import os.path
# from qc_linearity_sine_14bit import calc_linearity

types = ['rt_diff', 'rt_se', 'ln_diff', 'ln_se']

filenames = {}
filenames['rt_diff'] = glob.glob('coldadc_enr_3-*_rt_*/*_DIFF_dnl_inl.csv')
filenames['rt_se'] = glob.glob('coldadc_enr_3-*_rt_*/*_SE_dnl_inl.csv')
filenames['ln_diff'] = glob.glob('coldadc_enr_3-*_ln_*/*_DIFF_dnl_inl.csv')
filenames['ln_se'] = glob.glob('coldadc_enr_3-*_ln_*/*_SE_dnl_inl.csv')

COLUMNS = ['code', 'dnl', 'inlNorm', 'midADCmean', 'midADCstd']
# want to make:
# DataFrame with rows as chips and columns as code, dnl, inlNorm, midADCmean, midADCstd, anything else
# each of those has 16 numbers though (but maybe not "anything else")
# maybe multiindex dataframe? rows 1: chip. rows 2: each of 16 channels. columns: thingies.


def find_chipID(filename):
    '''find_chipID(filename) -> str
    Finds chipID string from full filename'''
    index = filename.find('enr_') + 4
    chipID = filename[index:filename.find('_', index)]
    return chipID

def calc_linearity(Codes16):
    '''calc_linearity(Codes16) -> (code, dnl, inlNorm, midADCmean, midADCstd
    Calculates linearity for an array of 16-bit codes Codes16
    Returns code (array), dnl (array), inlNorm (array), midADCmean (float), midADCstd (float)
    Somewhat copied from qc_linearity_sine_14bit.py'''
    Codes14 = Codes16 // 4
    sortCodes14 = np.sort(Codes14)
    minbin = sortCodes14[30]
    maxbin = sortCodes14[-30]
    yoffset = ((sortCodes14[1] + sortCodes14[-2]) / 2) - 8192
    minCodes16 = min(Codes16)
    maxCodes16 = max(Codes16)
    minCodes14 = min(Codes14)
    maxCodes14 = max(Codes14)
    print("Min/max code, spread (16bit)=", minCodes16, maxCodes16, maxCodes16 - minCodes16)
    print("Min/max code, spread (14bit)=", minCodes14, maxCodes14, maxCodes14 - minCodes14)
    print("Second Min/max code, offset (14bit)=", sortCodes14[1], sortCodes14[-2], yoffset)
    del sortCodes14

    bins = np.append(np.insert(np.arange(minbin, maxbin + 2) - 0.5, 0, 0.0), 16384.5)

    h, binedges = np.histogram(Codes14, bins)
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
    code = np.arange(minbin + TRUNC, maxbin - TRUNC + 1)

    return code, dnl, inlNorm, midADCmean, midADCstd

r = {}  # final result

for t in types:
    rfilename = t + '_pickle.bin'
    if os.path.exists(rfilename):
        r[t] = pd.read_pickle(rfilename)
    else:
        #count = 0
        results = {}
        for filename in filenames[t]:
            print(filename)
            chipID = find_chipID(filename)
            print(f'chipID: {chipID}')
            #resultfilename = filename[:-4] + '_stats.csv'
            #resultfilename = '/'.join(filename.split('/')[:-1] + 'dnl_inl_pickle.bin')
            resultfilename = 'dnl_inl_pickle_' + filename[:filename.rfind('/')] + '.bin'
            if os.path.exists(resultfilename):
                results[chipID] = pd.read_pickle(resultfilename)
                print(results[chipID])
            else:
                data = pd.read_csv(filename, header=None)
                del data[0]
                print('data:\n', data)
                result = data.apply(calc_linearity).T.rename_axis('Channel')
                result.columns = COLUMNS
                print(result)
                results[chipID] = result
                result.to_pickle(resultfilename)
            # DEBUG
            #count += 1
            #if count == 2:
            #    break
        print('Assembling database . . .')
        r[t] = pd.concat(results, copy=False, names=['ChipID', 'Channel'])
        print(r[t])
        print('Calculating dnlstd . . .')
        r[t]['dnlstd'] = r[t]['dnl'].map(np.std)
        print('Calculating maxinl . . .')
        r[t]['maxinl'] = r[t]['inlNorm'].map(np.max)
        print('Calculating mininl . . .')
        r[t]['mininl'] = r[t]['inlNorm'].map(np.min)
        print('Pickling . . .')
        r[t].to_pickle(rfilename)
    print(r[t])

# Stuff we need to calculate:
# Variation of DNL/INL across warm/cold, between chips
#   For this we need average DNL/INL across all chips of the same DIFF / SE for each channel
#   Then we find std deviation of the total to see how big the variance is
#   Maybe also plot DNL/INL values
# Variation between cold/warm measurements:
#   First, find out if chips with both types of data match with average? (for room temp)
#   For this, find average values (for each channel) for all chips and for just the ones with both
#       values, then see if difference is statistically significant
#   Then find difference between two temperature for each chip, for each channel
#   Overall statistic: average of these differences for each channel
#       Is average difference similar for each channel? Maybe also plot differences for each channel.
#       Check if variation among average differences between channels is statistically significant.

rfull = pd.concat(r, copy=False, axis=1)
print(rfull)
g = rfull.loc[:, (slice(None), ['dnlstd', 'maxinl', 'mininl'])].groupby(level='Channel')
#average = pd.concat({'Mean': g.mean(), 'Std': g.std()}, copy=False).unstack(level=0).T
#print(average)
#average.to_pickle('average_DNL_INL_pickle.bin')


datatypes = ['dnlstd', 'maxinl', 'mininl']
nbins = 50
plotranges = [(0.1, 0.25), (0, 25), (-25, 0)]

for t in types:
    f, ax = plt.subplots(16, 3, constrained_layout=True)
    f.set_size_inches(20, 50)
    f.suptitle(f'DNL and INL variation for each channel for test type {t}\n'
                'DNL Standard Deviation, Maximum INL, Minimum INL')
    
    for name, group in g:
        for statnum in range(3):
            if statnum == 0:
                ax[name - 1][statnum].set_ylabel(f'Channel {name}')
            # DEBUG
            print(f'statnum: {statnum}')
            sel = group.loc[:, (t, datatypes[statnum])].to_numpy()
            #print(sel)
            ax[name - 1][statnum].hist(sel, bins=nbins, range=plotranges[statnum])
    f.savefig(f'dnl_inl_plots_{t}.png')
