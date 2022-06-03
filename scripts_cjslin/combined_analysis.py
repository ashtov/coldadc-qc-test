import numpy as np
import matplotlib.pyplot as plt
import statistics
import os

def stats(parsed, keys, per_channel=True):
    def proc_samples():
        if not samples:
            return
        samples_proc = [list(s) for s in zip(*samples)]
        if ch is None:
            avgs[0].append([statistics.mean(s) for s in samples_proc])
            avgs[0][-1]+=[statistics.stdev(s) for s in samples_proc]
        else:
            avgs[ch].append([statistics.mean(s) for s in samples_proc])
        samples.clear()
    def proc_labels(v):
        if indice is None:
            return
        label = key_func(v)
        label = label[1:] if per_channel else label
        if label not in labels:
            labels.append(label)
    def key_func(v):
        ret=[]
        if per_channel:
            ret.append(v[0])
        for k in keys:
            ret.append(v[k])
        return tuple(ret)

    sorted_r = sorted(parsed[1:], key=key_func)
    indice = keys[-1] if keys else None
    x = None if indice is None else sorted_r[0][indice]
    ch = sorted_r[0][0] if per_channel else None
    avgs = [[] for i in range(16)] if per_channel else [[]]
    samples, labels = [], []

    proc_labels(sorted_r[0])
    for r in sorted_r:
        if indice is not None and r[indice] != x:
            proc_labels(r)
            proc_samples()
            x = r[indice]
        if ch is not None and r[0]!= ch:
            proc_samples()
            num_series = len(avgs[ch])
            num_conf = len(avgs[ch][0])
            ch = r[0]
        samples.append(r[4:])
    proc_samples()

    """ need to deal with missing channels when it happens
    """
    if per_channel:
        for i in range(16):
            if len(avgs[i]) == 0:
                avgs[i] = [[0 for i in range(num_conf)] for _ in range(num_series)]
    """
    avgs[0] = [[0] for _ in range(4)]
    avgs[8] = [[0] for _ in range(4)]
    """
    avgs = np.array(avgs).transpose(1,2,0)
    labels = ["All"] if not labels else ["-".join(label) for label in labels]
    return avgs, labels, per_channel

def grapher(data, labels, per_channel):
    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{0:.3f}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3 if height>0 else -10),  # 3 points vertical offset
                        size=6,
                        textcoords="offset points",
                        ha='center', va='bottom')
    x = np.arange(len(data[0][0]))
    width = 0.1
    offset = len(labels)*3/2
    offset = 0

    fig, ax = plt.subplots()
    title = 'Combined DNL/INL/ENOB (Warm)'
    ax.set_title(title)
    ax.set_ylabel(title)
    for i, lab in enumerate(labels):
        autolabel(ax.bar(x+(i-offset-1.5)*width, data[i][1], width, label="DNL_"+lab))
        autolabel(ax.bar(x+(i-offset-1.5)*width, data[i][0], width, label="DNL_"+lab))
        autolabel(ax.bar(x+(i-offset-.5)*width, data[i][3], width, label="INL_"+lab))
        autolabel(ax.bar(x+(i-offset-.5)*width, data[i][2], width, label="INL_"+lab))
        autolabel(ax.bar(x+(i-offset+.5)*width, data[i][4], width, label="ENOB_"+lab))
    if per_channel:
        ax.set_xlabel('Channel')
        ax.set_xticks(x)
        ax.legend(bbox_to_anchor=(1.1, 1.05))
    else:
        ax.set_xlabel('(Averaged over all channels)')
        ax.set_xticks([])
        #plt.xticks(x, ["Warm", "Cold"])
        ax.legend(bbox_to_anchor=(.9, .9))

    plt.show()

def find_chs(path):
    int_parser = lambda s: (int(s[0:2]), 2) if len(s)>1 and s[1].isdigit() else (int(s[0]), 1)
    ch_i = path.find("ch")+2
    ch, i = int_parser(path[ch_i:])
    adc0ch, adc1ch, misc = None, None, None
    if ch < 8:
        adc0ch = ch
    else:
        adc1ch = ch
    if len(path) > (ch_i+i) and path[ch_i+i] == "_" :
        if path[ch_i+i+1] == "v":
            misc = path[ch_i+i+1:ch_i+i+3]
        else:
            ch, i = int_parser(path[ch_i+i+1:])
            if ch < 8:
                adc0ch = ch
            else:
                adc1ch = ch
    return adc0ch, adc1ch, misc

def concat_images(imga, imgb):
    """
    Combines two color image ndarrays side-by-side.
    """
    ha,wa = imga.shape[:2]
    hb,wb = imgb.shape[:2]
    max_height = np.max([ha, hb])
    total_width = wa+wb
    new_img = np.zeros(shape=(max_height, total_width, 3))
    new_img[:ha,:wa]=imga
    new_img[:hb,wa:wa+wb]=imgb
    return new_img

def concat_n_images(image_path_list):
    """
    Combines N color images from a list of image paths.
    """
    output = None
    for i, img_path in enumerate(image_path_list):
        img = plt.imread(img_path)[:,:,:3]
        if i==0:
            output = img
        else:
            output = concat_images(output, img)
    return output

def concat_multi(inDir):
    concat_dir = "concat_graphs/"
    os.mkdir(concat_dir)
    for root, dirs, files in os.walk(inDir):
        if not files or files[0].find("Sinusoid") == -1:
            continue
        image_list = []
        for inFile in files:
            if inFile[-3:] =="png" and inFile.find("v1") != -1:
                image_list.append(root+'/'+inFile)
        image_list.sort()
        concat = concat_n_images(image_list)
        plt.imshow(concat)
        plt.axis('off')
        plt.savefig(concat_dir + "concat_"+root[len(inDir):].replace("/", "|") +".png", dpi = 500, bbox_inches='tight')


WARMDIFF = "data_ethlu/cold_diff/analysis/lin_graphs/"
#concat_multi(WARMDIFF)


            

if __name__=="__main__":
    import fft_test_multi as fft
    import calc_linearity_sine_multi as lin
    lin_data, lab = lin.single_stats(lin.parser(lin.WARM), False)
    fft_data, lab = fft.single_stats(fft.parser(fft.WARM), False)

    grapher(np.concatenate([lin_data, fft_data], axis = 1), lab, False)
