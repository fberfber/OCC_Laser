import numpy as np
import matplotlib.pyplot as plt
import cv2
#Algorithm for calibration of:
#    -Guard Time between frames  (tg)
#    -Readout Time Rate          (r)
#    -Effective Frame Rate Ratio (EFR) in %
img = cv2.imread("/home/fberfber/Desktop/app/output/test/videos/final/calibrationframe/frame"+str(0)+".png")
blue, green, r0= cv2.split(img)
for i in range(1,12,1):
    img = cv2.imread("/home/fberfber/Desktop/app/output/test/videos/final/calibrationframe/frame"+str(i)+".png")
    blue, green, r= cv2.split(img)
    r0= np.hstack((r0, r))
I = r0
# Perform the 2D Fourier Transform
# Step 2: Compute the 2D Fourier Transform
I_fft = np.fft.fft2(I)  # 2D Fourier Transform
I_fft_shifted = np.fft.fftshift(I_fft)  # Shift zero-frequency to the center
N = I_fft.shape[0]
frequencies = np.fft.fftfreq(N)  # Frequencies corresponding to the indices
frequencies = np.fft.fftshift(frequencies)  # Shift frequencies to center

# Compute the magnitude spectrum (Fourier magnitude)
magnitude_spectrum = np.abs(I_fft_shifted)

# Step 3: Marginalize over the temporal frequency axis (ω)
marginalized = np.sum(magnitude_spectrum, axis=1)  # Summing along rows (ω-axis) / Integrating 

plt.figure(figsize=(12, 6))

# Original spatiotemporal image
plt.subplot(1, 3, 1)
plt.imshow(I, aspect="auto", cmap="gray")
plt.title("Original Image I(y, t)")
plt.xlabel("Time (t)")
plt.ylabel("Space (y)")
plt.colorbar(label="Intensity")

# Magnitude spectrum of Fourier Transform
plt.subplot(1, 3, 2)
plt.imshow(np.log1p(magnitude_spectrum), cmap="gray", aspect="auto")
plt.title("Fourier Magnitude Spectrum")
plt.xlabel("ω (Temporal Frequency)")
plt.ylabel("ν (Spatial Frequency)")
plt.colorbar(label="Log Magnitude")

# Marginalized spectrum over ω
plt.subplot(1, 3, 3)
marginalized= marginalized[frequencies >= 0]
frequencies = frequencies[frequencies >= 0]  # Positive frequencies

plt.plot(frequencies,marginalized, color="blue")
f = np.argmax(marginalized)
plt.scatter(frequencies[f], marginalized[f], color = "red", label = "Laser frequency: "+str(np.around(frequencies[f],4)), linewidths=3)
plt.title("Marginalized Spectrum I(ν)")
plt.xlabel("Spatial Frequency (ν)")
plt.ylabel("Summed Magnitude")
plt.legend(fontsize = "15")
plt.tight_layout()
plt.show()
T_half_laser= 100 # in micro seconds
pixel_height = 864
r = frequencies[f]*2*T_half_laser
tf = 8324
te = 36
tg = tf - te - (pixel_height-1 )*r #where te is the exposure time of the first row 
print("Laser frequency (spatial) : ", frequencies[f], " pulses(0 or 1) per pixel row")
print("Row Readout Rate          : ",  frequencies[f]*2*T_half_laser," rows per μs" )
print("Guard Time (tg)           : ", tf - te - (pixel_height-1 )*r," μs")
print("Effective Frame Rate Ratio: ", np.around(tf/(tf+tg) ,3)*100, "%")