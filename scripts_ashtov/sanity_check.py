#!/usr/bin/env python3

import glob
import numpy as np
import pandas as pd
import qc_dnl_inl_newer

chipID = '3-170'
infilename = glob.glob(f'../test_results/coldadc_enr_{chipID}*/rawLinDataDiff.csv')[0]

a = pd.read_csv(infilename, quoting=3, skiprows=1, header=None, converters={2: lambda x: np.uint8(x[2:]), 65537: lambda x: np.uint8(x[:-2])}, dtype=np.uint8).loc[slice(None), 2:].astype('uint8')
print(a)
print(a.dtypes)
b = a.to_numpy()
print(b)
c = b.flatten()
print(c)

qc_dnl_inl_newer.calc_plot_dnl_inl(c, dirsave='sanity_check', asicID=chipID, NumSet=480)
