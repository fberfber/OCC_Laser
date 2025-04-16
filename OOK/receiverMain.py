import cv2
import numpy as np 
import matplotlib.pyplot as plt
import scipy
from itertools import groupby
from scipy.signal import find_peaks
import scipy.ndimage
from reedsolo import RSCodec
from send_OOK import encode
import framesManager
# Path to the folder
from pathlib import Path
from videoRec import capture_data
from time import time

filename = input("Type the filename of the .mp4 captured video, or press ENTER to capture a new video: ")
path = "videos/"+filename+".mp4"
t0 = time()
if filename=="":
    t0 = time()
    filename = input("Type the filename of the newly .mp4 captured video")
    path = "videos/"+filename+".mp4"
    capture_data(path)

framesManager.EmptyFolder("/home/fotisber/Desktop/OCC_Laser/input_frames")
framesManager.FrameCapture(path)
t1= time()
folder_path = Path("/home/fotisber/Desktop/OCC_Laser/input_frames")
# Count the number of files in the folder
num_files = len([f for f in folder_path.iterdir() if f.is_file()])
sampled_packets = []
duration_0 =[]
duration_1 = []
def preprocess_frame(frame,sigma, plot):
    """
    Preprocess includes averaging per row, gaussian filtering\n 
    and spatially adaptive thresholding.
    """
    _,_,r       = cv2.split(frame)
    re = cv2.rotate(r, cv2.ROTATE_90_COUNTERCLOCKWISE)
    signal_0    = np.mean(r,axis = 1)
    if plot:
        plt.figure("On Off Keying")
        plt.subplot(4,1,1)
        plt.title("Input Frame")
        plt.imshow(re, cmap = "gray")
        plt.subplot(4,1,2)
        plt.title("Row Mean Average")
        plt.plot(signal_0)
    #Filter high frequency noise
    signal_gaussian = scipy.ndimage.gaussian_filter1d(signal_0, sigma)
    if plot:
        plt.subplot(4,1,3)
        plt.title("Noise Filtered Signal")
        plt.plot(signal_gaussian/np.max(signal_gaussian))
    threshold_signal = np.ones(864,dtype = int)
    for i in range(0,864,216):
        area = signal_gaussian[i:i+216]
        
        threshold = np.max(area)/2
        if threshold>20:
            threshold_signal [i:i+216][area<0.8*threshold]=0
        else:
            threshold_signal[i:i+216] = 0
    return threshold_signal
def calibrate_pulsewidth(processed_frame):
    """
    Calibrates the pulsewidth of 0 and 1 sequencies
    for a given frame. Used to calibrate the sampling process.
    """
    durations = []
    starts = []
    i = 0
    for key,group in groupby(processed_frame):
        length=sum(1 for _ in group)
      
        if key==0 :
            durations.append(length)
            starts.append(i)
        i += length
    return starts, durations
def extract_packet_sequencies(processed_frame, starts, durations, plot, jump):
    markers_end =[]
    markers_start = []
    packets = [] 
    s0 = 0
    c  = 0
    print(f"FRAME {f} :  ", end = '')
    if plot:
        plt.subplot(4,1,4)
        plt.title("Filtered Signal")
        plt.plot(processed_frame)
    # Raises TIMEOUT when data is not received before the maximun A.T (Jump).
    if jump is not None:
        start = max(jump-20,0)
        end =min(jump+20,863)
        if np.average(processed_frame[start:end])<0.005:
            print(f"TIMEOUT")
            packets.append([1001])
            jump = None
    # -------------------------------------------------------------
    # 1ST-Stage sequence seperation: START MARKERS
    c=0
    for i, d in enumerate(durations):
        
        if d>=90 and d<100 and starts[i]+d+120<864:
            if c==0:
                s0 = i
            markers_start.append(starts[i]+d)
            c=1
    # -------------------------------------------------------------
    if len(markers_start)==0:
        print(f"TIMEOUT ")
        if plot:
            plt.show()
        return [[1001]], None
    if starts[0]==0 and durations[0]+200<markers_start[0] and (durations[0] not in markers_start):
        markers_start = [durations[0]]+markers_start
        s0 = 0

    # 2ND-Stage sequence seperation: END MARKERS
    for i, d in enumerate(durations):
        if d>=90 and d<100 and i>s0 and starts[i]-120>0:
            markers_end.append(starts[i])
    if markers_start[-1]+120<864 and len(markers_start)!=len(markers_end):
        markers_end.append(starts[-1])
    # -------------------------------------------------------------

    # Checks for close miss on first packet
    if (jump is not None) and jump <15:
        if markers_start[0]>30:
            packets.append([1002])
    
    last_byte_time = 36 + 9*(markers_end[-1]-1)
    Tg = 521 # FRAME GAP TIME
    Tf = 8324 #TOTAL FRAME DURATION (GAP + EFFECTIVE)

    next_byte_start = last_byte_time + 10*108
    next_byte_end   = last_byte_time + 18*108


    i = 0
    
        #plt.scatter(markers,processed_frame[markers])
    while i<len(markers_end) :
        try:
            if markers_end[i]-markers_start[i]>110:
                packets.append(processed_frame[markers_start[i]:markers_end[i]])
            else:
                pass
        except:
            plt.show()
        if plot:
            plt.subplot(4,1,4)
            plt.plot([markers_end[i], markers_end[i]],[0,1], color = "black", linestyle="--", linewidth =3)
            plt.plot([markers_start[i], markers_start[i]],[0,1], color = "green", linestyle="--", linewidth =3)
        i+=1
    if plot and jump is not None:
        plt.subplot(4,1,4)
        plt.plot([jump,jump],[0,1],color = "red", linewidth = 3 )

       
    if (next_byte_start>=Tf and next_byte_end>=Tf) :
        lost_packet = False
        t0 = next_byte_start - Tf
        jump = int((t0-36)/9 + 1)
        print(f"NO PACKETS LOST, expected JUMP at ROW {jump}")
    elif (next_byte_start<Tf -Tg and next_byte_end<Tf -Tg  ):
        packets.append([1001])
        jump = None
        lost_packet = False
        print("TIMEOUT")
    else:
        t0 = next_byte_end - Tf +10*108
        jump = int((t0-36)/9 + 1)
        packets.append([1002])
        print(f"PACKET LOST, expected JUMP at ROW {jump}")
        lost_packet = True
    if plot:
        #plt.plot([markers_end[-1], markers_end[-1]],[0,1], color = "green", linestyle="--", linewidth =3)
        pass
        #plt.plot([markers[-1], markers[-1]],[0,1], color = "black", linestyle="--", linewidth =3)
    if lost_packet:
        #packets.pop()
        if plot:
            plt.subplot(4,1,4)
            plt.scatter(863,processed_frame[863],marker = "o", color = "red")

    if plot:
        plt.show()
    return packets, jump
def compare_with(word, nsyn):
        dataTx = word.encode("utf-8")
        dataTx_bits = ''.join(format(byte, '08b') for byte in dataTx)
        rsc = RSCodec(nsyn)
        enc = rsc.encode(dataTx)
        dataTx_bits = ''.join(format(byte, '08b') for byte in enc)
        return dataTx_bits
def demodulate_OOK(data_packets):
   
    #!_______________________________
    switch = True
    demodulated_data =[]
    demodulated_bitstream = []

    data_packets.append([1001])

    for data in data_packets:
    
        if data[0]==1001 and switch:
            demodulated_bitstream.append(demodulated_data)
            demodulated_data = []
            switch = False
        elif data[0]==1002:
            switch = True
            demodulated_data.append("XXXXXXXX")
        else:
            switch = True
            samples = np.array_split(data,10)
            demodulated_packet=""
            for i,s in enumerate(samples):
                if i!=0 and i!=len(samples)-1:
                    s = list(s)
                    if s.count(0)>=s.count(1):
                        demodulated_packet+="0"
                    else:
                        demodulated_packet+="1"
            
            demodulated_data.append(demodulated_packet)
    return demodulated_bitstream
def decode_ReedSolo(demodulated_bitstream):
    messages = []

    for index , stream in enumerate( demodulated_bitstream ):
        i = 0
        RSencoded = []
        erase_pos = []
        flag_nsyn = False
        if stream:
            
            for packet in stream:
                
                if i==0:
                    if packet =="XXXXXXXX":
                        flag_nsyn = True
                        continue
                    nsyn = int(packet,2)
                elif i==1 : 
                    if flag_nsyn:
                        nsyn = int(packet,2)
                    else:
                        if packet!="XXXXXXXX":
                            nsyn_2 = int(packet,2)
                            if nsyn_2!=nsyn:
                                RSencoded.append(packet)
                        else:
                            pass
                
                else:
                    if packet!= "XXXXXXXX":
                        RSencoded.append(packet)
                    else:
                        erase_pos.append(len(RSencoded))
                        RSencoded.append("00000000")
                i+=1
 
            rsc = RSCodec(nsyn)

            enc_bytes = bytearray()
            i = 0
            for enc_byte in RSencoded:

                enc_bytes.append(int(enc_byte,2))
            output = rsc.decode(enc_bytes, erase_pos=erase_pos)
            word = output[0].decode('utf-8', errors='ignore')
            messages.append(word)
    return messages

data_packets = []
packets_loss = 0
jump = None
lengths = []
for f in range(0,num_files,1):
    
    plot = False
    processed_frame = preprocess_frame(cv2.imread(f"input_frames/frame{str(f)}.jpg"),sigma=1, plot  = plot)
    starts, durations = calibrate_pulsewidth(processed_frame)
    packets, jump= extract_packet_sequencies(processed_frame,starts, durations, jump=jump, plot = plot)
    for n , p in enumerate(packets):
        data_packets.append(p)


demodulated_bitstream = demodulate_OOK(data_packets)
messages = decode_ReedSolo(demodulated_bitstream)
t2 = time()
bits = 0
for i, m in enumerate(messages):
    print(f"Message {m} : ",m)
    dataTx = m.encode("utf-8")
    dataTx_bits = ''.join(format(byte, '08b') for byte in dataTx)
    bits+=len(dataTx_bits)
Tproc = np.around(t2-t1,4)
Ttot = np.around(t2-t0,4)
R = bits/(Ttot+3)
print(f"Processing time : {Tproc} seconds")
print(f"Total runtime   : {Ttot } seconds")
print(f"Bit Rate        : {R} bits/s")