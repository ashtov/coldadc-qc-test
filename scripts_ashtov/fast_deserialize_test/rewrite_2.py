import numpy as np
import pandas as pd

c = np.fromfile('LinDataDiff_deserialized.bin', dtype=np.uint16)
print(c)
d = c.reshape(983040, 16)
print(d)
for i in range(3):
    print(list(d[i]))
