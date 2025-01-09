import numpy as np
import cv2
from scipy.signal import find_peaks
from matplotlib import pyplot as plt
from matplotlib.pyplot import plot as plot
from matplotlib.pyplot import show as show
from matplotlib.pyplot import scatter as scatter
from matplotlib.pyplot import figure as figure

#A 1 11 111 1111 sequence is sent repeatedly to calculate the pixel height of each pulse 

# Each symbol is seperated with a '0' that is detected by detecting the valleys  (inverted peaks)
tot = 0
cor = 0
y = [[],[],[],[]]# each indexed list will store the pixel heights of T, 2T, 3T, 4T
#frame height: 864
#T = 56us
#Shot on Rpi cam module 3 wide at 120fps
for frame in range(16):
    num = str(frame)
    #pre processing
    img = cv2.imread("/home/fberfber/Desktop/app/output/test/videos/final/equation/frame"+num+".png")#set path 
    blue, green, r= cv2.split(img)
    r_mean = np.mean(r, axis =1)
    output = r_mean
    #plot(output)
    #--------------
    #widths measuring
    lows, _ = find_peaks(-output,distance =4, prominence=6) #find the 0s
    lows = [i for i in lows if 1< output[i] < 128]
    #scatter(lows,output[lows], color = "red")
    #show()
    widths = np.diff(lows)
    widths = [widths[i] for i in range(len(widths)) if 10 < widths[i] < 41] #skip any errors(odd values)
    wlows, _ = find_peaks(-np.asarray(widths),height = (-15,0))# find the '1' sequencies, used in the following loop
    widths = np.asarray(widths)

    for i in range(4):
        for w in wlows:
            try:
                y[i].append(widths[w+i])
            except:
                pass
    #-------------- 
c=0 
#results
print("Total samples ", len(y[0]))
print("Mean Symbol Pixel Height")
for k in y:
    print(str(c+1)+"T Height: ",np.mean(k))
    c+=1
print("Standard Deviation")
c = 0
for k in y:
    print(str(c+1)+"T std.: ",np.std(k))
    c+=1
c = 0
symbols = ["s0", "s1", "s3", "s2"]
for k in y:
    hist, bin_edges = np.histogram(k, bins=len(k), density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    plt.plot(bin_centers, hist, label="P.M. of "+symbols[c], linestyle="-" )
    c+=1

plt.xlabel("Value",fontsize = 23)
plt.ylabel("Probability",fontsize = 23)
plt.title("Probability Metrics (P.M.)",fontsize = 23)
plt.legend(fontsize = 23)
plt.grid(True)
plt.show()