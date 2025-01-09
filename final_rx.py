import numpy as np
import cv2
from scipy.stats import norm
from scipy.signal import find_peaks
from matplotlib import pyplot as plt
from matplotlib.pyplot import plot as plot
from matplotlib.pyplot import show as show
from matplotlib.pyplot import scatter as scatter
from matplotlib.pyplot import figure as figure
#This is a trial for testing the perfomance of the modulation scheme, with no error correction implemented. 
#We try to transmit the codework "check"

x ="0110001101101000011001010110001101101011" # word "check" in binary form (decoded form)
index = range(864) #frame height
img = cv2.imread("output/test/videos/final/check.png")
blue, green, r= cv2.split(img)
r_mean = np.mean(r, axis =1)
output = r_mean
lows, _ = find_peaks(-output,distance =4, prominence=6) # seperate the symbols
lows = [i for i in lows if 1< output[i] < 100] #filter wrong valleys

demodulated = ""
widths = np.diff(lows)
widths = np.asarray(widths)

for i in range(0,len(widths),1):
        pixel_height = widths[i]
    
        period = int(round((pixel_height - 12)/6.285)) #from final_length.py 
        
        demodulated += bin(period)[2:].zfill(2)

print("Demodulated data: ",demodulated)
print("Input data      : ",x)
bytes = int(demodulated, 2).to_bytes((len(demodulated) + 7) // 8, byteorder='big') #to bytes
text = bytes.decode('utf-8')  #Decoding from bytes to text
print("Codeword: ",text)
plt.scatter(lows,output[lows], color = "red")
plt.plot(index, output)
plt.show()
