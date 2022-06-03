import matplotlib.pyplot as plot
import numpy as np

if __name__ == "__main__":
    vals = []
    occupancy = [0] * (2**14)
#    text_file = open('data/RT_Diff_PKG46_06-28-2021/Sinusoid_147KHz_Diff_NomVREFPN_1M_ch2_v2.txt', 'r')
    text_file = open('temp_2M.txt', 'r')
    for row in text_file:
        vals.append(int(row) / 4.0)
        occupancy[int(row) / 4] += 1
    print(np.std(occupancy[8000:8800]))
    plot.hist(vals,bins=2**14,range=(-0.5,16383.5))
    plot.xlim(-0.5,16383.5)
    plot.ylim(0,300)
    plot.xlabel("ADC Value")
    plot.ylabel("Counts")
    plot.savefig("ADCValues.png", dpi=300)
    plot.xlim(8000,8800)
    plot.ylim(0,120)
    plot.savefig("ADCValues_Zoom.png", dpi=300)
    plot.clf()
    plot.hist(occupancy,bins=100,range=(0,100))
    plot.xlim(20,95)
    plot.xlabel("Occupancy")
    plot.ylabel("Number of ADC Values")
    plot.savefig("ADCOccupancy.png", dpi=300)
    plot.clf()
    plot.hist(occupancy[6000:10000],bins=80,range=(50,130))
    plot.xlabel("Occupancy")
    plot.ylabel("Number of ADC Values")
    plot.title("Occupancy Numbers for ADC Bins 6000 to 10000")
    plot.savefig("ADCOccupancy_MiddleADCs.png", dpi=300)
    
