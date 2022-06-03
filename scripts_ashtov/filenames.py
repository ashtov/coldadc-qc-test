import glob

g = glob.glob('coldadc_enr_3-*/*')
h = []
for i in g:
    index = i.index('-') + 1
    index2 = i.index('_', index)
    chipID = int(i[index:index2])
    if (chipID < 29 or chipID > 70) and i[-8:] != 'Diff.csv' and i[-6:] != 'SE.csv':
        h.append('-lmkdir ' + i[:i.rindex('/')] + '\nget -a ColdADC/test_results/' + i + ' ' + i)

with open('filelist.txt', 'w') as f:
    f.write('\n'.join(h))
