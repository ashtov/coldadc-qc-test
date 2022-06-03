import sys, os, csv, statistics
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from scipy.optimize import curve_fit
from scipy.stats import norm
import numpy as np
import fft_test as fft

EXTREMA = [1, 5, 10]
MAX_E = max(EXTREMA)

def process(inFile, maxs = False, plot=False):
    print("Input file name : ",inFile)
    y0 = np.loadtxt(inFile, dtype=int)
    if not maxs: 
        y0 = y0[:2048]
        x0 = np.arange(0, 2048)*1./2E6 
        ret = sine_fit(x0, y0, plot)
        plt.show()
        return ret
    else:
        inds = np.argpartition(y0, -maxs)[-maxs:]
        #inds = inds[np.argsort(y0[inds])]
        inds = np.sort(inds)
        inds_gp, inds_gp_count = [[inds[0]]], [1]
        for i in range(1, maxs):
            ind = inds[i]
            if ind - inds_gp[-1][0] < 2048:
                inds_gp[-1].append(ind)
                inds_gp_count[-1]+=1
            else:
                inds_gp.append([ind])
                inds_gp_count.append(1)
        #print(inds_gp)
        inds = [int(np.average(gp)) for gp in inds_gp]
        #print(inds_gp_count)
        count = 0
        count_inds = []
        for ind in inds:
            ind_min = max(0, ind-1024)
            ind_max = min(len(y0), ind+1024)
            x0 = np.arange(ind_min, ind_max)*1./2E6 
            res_min, res_max= sine_fit(x0, y0[ind_min: ind_max], False )
            if res_max[0] > 10000:
                count+=1
                count_inds.append(ind)
                sine_fit(x0, y0[ind_min: ind_max], plot)
        plt.show()
        return count, np.sort(count_inds)

def sine_fit(x0, y0, plot=False):
    # create the function we want to fit
    def my_sin(x, freq, amplitude, phase, offset):
        return np.sin(x * freq + phase) * amplitude + offset

    #guess_freq = 147460.0 * (2.0*np.pi)   # ADC only FFT
    guess_freq = 20507.8 * (2.0*np.pi)     # Single Channel Full-Chain FFT
    #guess_freq = 10507.8 * (2.0*np.pi)     # Single Channel Full-Chain FFT

    guess_amplitude = (y0.max()-y0.min())/2.0
    guess_phase = 0
    guess_offset = np.mean(y0)

    #print("Max, Min ADC =",y0.max(), y0.min())

    NoiseStudy = 0
    if NoiseStudy == 0 :

        p0=[guess_freq, guess_amplitude, guess_phase, guess_offset]
        # now do the fit
        fit = curve_fit(my_sin, x0, y0, p0=p0)

        # we'll use this to plot our first estimate. 
        data_first_guess = my_sin(x0, *p0)

        # recreate the fitted curve using the optimized parameters
        data_fit = my_sin(x0, *fit[0])

        # residual (data - fit)
        residual = y0 - data_fit
        #print("Max, min residuals = ",residual.max(),residual.min())
        print(fit[0])

        residual_min, residual_max = [], []
        residual_mins = np.sort(residual[np.argpartition(residual, MAX_E)[:MAX_E]])
        residual_maxs = np.sort(residual[np.argpartition(residual, -MAX_E)[-MAX_E:]])
        for e in EXTREMA:
            residual_min.append(np.average(residual_mins[:e]))
            residual_max.append(np.average(residual_maxs[-e:]))

        if plot: 
            #Setup plot
            #style.use('fivethirtyeight')
            fig = plt.figure()
            ax1 = fig.add_subplot(2,1,1)
            #plt.xlabel('Time (Sec)')
            plt.ylabel('ADC Count')
            #plt.title('Sinusoidal Input (152KHz; Vp-p 1.5V)')
            #plt.title('Sinusoidal Input (17KHz; Vp-p 1.5V)')
            #plt.title('Sinusoidal Input (LN2; 20.5KHz; Vp-p 1.4V;Full Chain; VDDD=2.0V, VDDA=2.5V (Reg0=0x62,Reg4=0x33))')
            #plt.title('Sinusoidal Input (LN2; 20.5KHz; Vp-p 1.4V;SingleEnded SHA-ADC (Reg0=0x63,Reg4=0x3B))')
            #plt.title('Sinusoidal Input (147KHz; Vp-p 1.4V; ADC Only; Nominal CMOS VREF) ')
            #plt.title('Sinusoidal Input (147KHz; Vp-p 1.0V; ADC Only; VREFN/P +/-200mV; Reg23=0x30; Room Temp) ')
            #plt.title('Sinusoidal Input (147KHz; Vp-p 1.5V; ADC Only; Nom CMOS VREF; VDDA2P5=2.5V; Room Temp) ')
            plt.title('Sinusoidal Input (20.5KHz; Vp-p 1.4V; ADC Only; Nom CMOS VREF) ')

            ax1.plot(x0,y0,'.',label='ADC Output')
            ax1.plot(x0,data_fit, label='Fit')
            #ax1.plot(x0,data_first_guess, label='first guess')
            ax1.legend(loc='upper right')
     
            ax2 = fig.add_subplot(2,1,2)
            plt.xlabel('Time (Sec)')
            plt.ylabel('Residuals (16-bit)')
            ax2.plot(x0,residual,'.')
    else:
        ax1 = fig.add_subplot(1,1,1)
        #histTitle="Noise Measurement (ADC Only; VDDA2p5=2.25V; At -70"+chr(176)+"C)"
        histTitle="Noise Measurement (ADC Only; VDDA2p5=2.5V; Room Temperature)"
        #histTitle="Noise Measurement (ADC Only; VDDA2p5=2.25V; LN2 Temperature)"
        plt.title(histTitle)
        plt.ylabel('Counts')
        plt.xlabel('ADC Channel')
        histResults=plt.hist(y0,bins=21, align='mid')
        #histResults=plt.hist(y0,bins=30)
        
        # now do the fit
        mean,std = norm.fit(y0)
        xmin,xmax = plt.xlim()
        #xtmp = np.linspace(xmin,xmax,100)
        xtmp = histResults[1]
        ytmp=norm.pdf(xtmp,mean,std)
        #hRatio=sum(histResults[0])/sum(norm.pdf(histResults[1],mean,std))
        hRatio=sum(histResults[0])/sum(ytmp)
        plt.plot(xtmp,(ytmp*hRatio))
        stdNoise= std * (3.0/2**16) * 10**6

        printMu="Mean = %6.1f "% (mean)
        printWid="Sigma = % 3.2f" % (std)
        printNoise="Noise = %4.1f $\mu$V" % (stdNoise)
        plt.gcf().text(0.65,0.7,printMu)
        plt.gcf().text(0.65,0.65,printWid)
        plt.gcf().text(0.65,0.60,printNoise)
        #plt.text(32685,1500,printWid)
        print("Noise mean, std =", mean, std)
        
    #plt.savefig('{}.png'.format(inFile[inFile.rindex('/')+1:]), dpi=500)

    # Run FFT
    #fft.AnalyzeDynamicADCTest(y0)
    return [residual_min, residual_max]

#process("data_ethlu/warm/ch3_11/Sinusoid_20KHz_SE-SHA-ADC0_NomVREFPN_2M_v2.txt")
process("data_ethlu/warm_diff/ch0/ADC0_Sinusoid_20KHz_DBypass-FrozenSHA_NomVREFPN_2M_v2.txt", plot=True)

#print(process("data_ethlu/ch0_8/Sinusoid_20KHz_SE-SHA-ADC1_NomVREFPN_2M_v1.txt", 100)[0])
#print(process("data_ethlu/ch1_9/v1/Sinusoid_20Khz_SDC-SHA-ADC0_NomVREFPN_2M_v1.txt", 100)[0])

def process_multi(inDir):
    output = open("sine_fit_analysis.csv", "a+")
    writer = csv.writer(output)
    writer.writerow([inDir, "residual_mins", "residual_maxs", EXTREMA])

    for buff in ["SE-", "SDC-"]:
        for mux in ["SHA-", "FrozenSHA-"]:
            for adc in ["ADC0_", "ADC1_"]:
                for v in ["v1.txt", "v2.txt"]:
                    inFile = "Sinusoid_20Khz_"+buff+mux+adc+"NomVREFPN_2M_"+v
                    writer.writerow([inFile] + process(inDir+inFile))

    output.close()

def parser(sine_fit_file):
    with open(sine_fit_file, 'r') as f:
        reader = csv.reader(f)
        parsed = [["Channel", "SDC/SE","Frozen/SHA", "residual_mins", "residual_maxs"]]
        for r in reader:
            r_p = []
            if r[1] == "residual_mins":
                channels = int(r[0][r[0].find("ch")+2])
                no_cal = "NoCal" in r[0]
            else:
                if no_cal:
                    continue
                header = r[0]
                if "ADC0" in header:
                    r_p.append(channels)
                else:
                    r_p.append(channels+8)
                if "SDC" in header:
                    r_p.append("SDC")
                else:
                    r_p.append("SE")
                if "FrozenSHA" in header:
                    r_p.append("FrozenSHA")
                else:
                    r_p.append("SHA")
                for i in range(1,3):
                    extremas = [float(s) for s in r[i][1:-1].split(',')]
                    r_p.append(extremas[1])
                parsed.append(r_p)

    """
    with open("linearity_parsed.csv", "w+") as f:
        writer=csv.writer(f)
        writer.writerows(parsed)
    """
    return parsed

def grapher(parsed):
    sorted_r = sorted(parsed[1:], key=lambda x: x[0:3])
    avgs = [[] for _ in range(16)]
    ch, sha = 0, "FrozenSHA"
    samples = []
    for r in sorted_r:
        if r[2] != sha:
            sha = r[2]
            samples = [list(s) for s in zip(*samples)]
            avgs[ch].append([statistics.mean(s) for s in samples])
            samples = []
        if r[0] != ch:
            ch = r[0]
        samples.append(r[3:5])
    samples = [list(s) for s in zip(*samples)]
    avgs[ch].append([statistics.mean(s) for s in samples])

    for i in range(16):
        if not avgs[i]:
            avgs[i] = [[0,0] for _ in range(4)]

    avgs = np.array(avgs).transpose(1,0,2)

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{0:.2f}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3 if height>0 else -10),  # 3 points vertical offset
                        size=6,
                        textcoords="offset points",
                        ha='center', va='bottom')

    x = np.arange(16)
    width = 0.2

    fig, ax = plt.subplots()
    ax.set_ylabel('(Averaged) Extrema Sine Fit Residual (16 bit)')
    ax.set_xlabel('Channel')
    ax.set_xticks(x)
    ax.set_title('(Averaged) Extrema Sine Fit Residual (16 bit)')
    autolabel(ax.bar(x-1.5*width, avgs[0][:,1], width, label='SDC-FrozenSHA'))
    autolabel(ax.bar(x-.5*width, avgs[1][:,1], width, label='SDC-SHA'))
    autolabel(ax.bar(x+.5*width, avgs[2][:,1], width, label='SE-FrozenSHA'))
    autolabel(ax.bar(x+1.5*width, avgs[3][:,1], width, label='SE-SHA'))
    autolabel(ax.bar(x-1.5*width, avgs[0][:,0], width, label='SDC-FrozenSHA'))
    autolabel(ax.bar(x-.5*width, avgs[1][:,0], width, label='SDC-SHA'))
    autolabel(ax.bar(x+.5*width, avgs[2][:,0], width, label='SE-FrozenSHA'))
    autolabel(ax.bar(x+1.5*width, avgs[3][:,0], width, label='SE-SHA'))
    ax.legend(bbox_to_anchor=(1.1, 1.05))

    plt.show()

sine_fit_statistics = lambda lin_file: grapher(parser(lin_file))

if __name__!="__main__":
    BASE = "data_ethlu/"
    for ch in range(0, 8):
        inDir = BASE+"ch{}_{}/".format(ch, ch+8)
        try:
            process_multi(inDir)
        except Exception as e:
            print("bad inDir", inDir)
            print(e)
        for inDir in os.scandir(inDir):
            if inDir.is_dir():
                try:
                    process_multi(inDir.path+'/')
                except Exception:
                    print("bad inDir", inDir.path)
#sine_fit_statistics('data_ethlu/analysis/sine_fit_analysis.csv')
#print(process("data_ethlu/warm_2/ch2_10/ADC0_Sinusoid_20KHz_SDC-FrozenSHA_NomVREFPN_2M_v2.txt", plot=True))
print(process("data_ethlu/warm/ch1_9/v1/Sinusoid_20KHz_SDC-SHA-ADC1_NomVREFPN_2M_v2.txt", plot=True))
