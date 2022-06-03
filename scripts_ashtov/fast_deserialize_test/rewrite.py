import numpy as np
import pandas as pd
#import itertools


# not faster
#a = pd.read_csv('rawLinDataDiff.csv', quoting=3, skiprows=1, header=None).loc[slice(None), 2:]
#b = a.loc[slice(None), [2, 65537]]

# didn't finish after 2 minutes
#a = np.genfromtxt('rawLinDataDiff.csv', skip_header=1, deletechars='"[]', dtype='int', autostrip=True)

#c = a.squeeze()
#print(c)
#b = pd.DataFrame.from_records((itertools.zip_longest(c)))
#print(b)
#d = np.loadtxt('rawLinDataDiff.csv', dtype='int', usecols=2, delimiter=',', skiprows=1, converters={2: lambda x: x.removeprefix('"[').removesuffix(']"')})
#print(d)

a = pd.read_csv('rawLinDataDiff.csv', quoting=3, skiprows=1, header=None, converters={2: lambda x: np.uint8(x[2:]), 65537: lambda x: np.uint8(x[:-2])}, dtype=np.uint8).loc[slice(None), 2:].astype('uint8')
print(a)
print(a.dtypes)
b = a.to_numpy()
print(b)
b.tofile('rawLinDataDiff.bin', sep='')

# what we want to do:
# original logic:
#   with list of lists iBlock (480 lists)
#   for each list (aka sample?):
#       so we only need to worry about iterating over a list
#      for each of 65536 integers within, iterating over output by 1 (also iBit?):
#          append to the output the complicated bitwise thing, and also to output+8 index
#           do this for 4 samples, decrementing iBit
#           after that, go ahead by a channel (unless it's multiple of 8, then go ahead by 8)
#           end up with 32768 deserialised thingies
# end up with list of lists again (or just a big list?)
# eventually we want to take every 16th value

# start with 480 sets of samples with 65536 samples each (8 bits)
# 4 samples -> pair of channel values (16 bits)
# 16 channels (8 pairs)

# new logic:
# with a list of samples 65536 long, 8 bit integers
# pivot 4-wise I guess (now 4 x 16384): each row will become two channels
# operate on each row, producing two columns out of four
# or maybe pivot 32-wise (now 32 x 2048): each row will become 16 channels (which is what we want)
# for each row:
#   repivot 4-wise (4 x 8)
#   for each row within:
#       A1 B1 C1 D1 E1 F1 G1 H1  A2 B2 C2 D2 E2 F2 G2 H2  A3 B3 C3 D3 E3 F3 G3 H3  A4 B4 C4 D4 E4 F4 G4 H4 
#       D1 D2 D3 D4 C1 C2 C3 C4  B1 B2 B3 B4 A1 A2 A3 A4  H1 H2 H3 H4 G1 G2 G3 G4  F1 F2 F3 F4 E1 E2 E3 E4
#   this can be 32 at a time, I think

#def deserialize_sample(in_array):
#    '''deserialize_sample(in_array) -> uint16[16]
#    Deserializes a uint8[32] array to a uint16[16] array
#    '''
#    result = np.empty((16, 2), dtype=np.uint16)
#    
