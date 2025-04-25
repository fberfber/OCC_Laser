import cv2
import numpy as np 
import matplotlib.pyplot as plt
import scipy
from itertools import groupby
from scipy.signal import find_peaks
import scipy.ndimage
from reedsolo import RSCodec
import reedsolo
from send_OOK import encode
import framesManager
from datetime import datetime
from pathlib import Path
import videoRec
import time
import lzma
import logging

import os
logging.basicConfig(level=logging.INFO)



def preprocess_frame(frame,sigma, plot):
    """
    Preprocess includes: Averaging per row, Gaussian filtering\n 
    and Spatially adaptive thresholding.
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
def extract_packet_sequencies(processed_frame, starts, durations, jump,f ,check_empty,plot =False):
    if plot:
        plt.subplot(4,1,4)
        plt.title("Filtered Signal")
        plt.plot(processed_frame)
    markers_end =[]
    markers_start = []
    add_timeout = False
    packets = [] 
    close_miss_check = False
    pop = False
    timed_out = False
    Tg = 521 # FRAME GAP TIME
    Tf = 8324 #TOTAL FRAME DURATION (GAP + EFFECTIVE)
    s0 = 0
    c  = 0
    print("_"*80)
    print("")
    print(f"FRAME {f} :")
    if np.max(processed_frame)==0:
        if check_empty:
            return [[1001]], None, False, True
        else:
            return [[1001]], None, False, False

    if (jump is not None) and jump<10:
        if jump<0:
            jump = 0
        close_miss_check = True
 
        
    time_out_index = None
    # 1ST-Stage sequence seperation: START MARKERS
    c=0
    for i, d in enumerate(durations):
        
        if d>=90 and d<100 and starts[i]+d+120<864:
            if timed_out and durations[i+1]>200:
                #   This handles the case where a GAP sequence is left alone 
                #in a timeout zone, so that it is not incorrectly detected
                continue
            if c==0:
                s0 = i
            markers_start.append(starts[i]+d)
            c=1
        elif d>100:
            time_out_index = starts[i]
        else:

            pass
    # -------------------------------------------------------------


    if (time_out_index is not None) and len(markers_start)==0:
        
        if time_out_index ==0:
            if check_empty:
                pop = True
            last_byte_time = 36 + 9*(durations[0]-1)
            next_byte_start = last_byte_time + 10*108
            next_byte_end   = last_byte_time + 18*108
            if (next_byte_start>=Tf and next_byte_end>=Tf) : 
                t0 = next_byte_start - Tf
                print("TIMEOUT - 3001")
                jump = int((t0-36)/9 + 1)
                print(f"Packet JUMP - expected JUMP at ROW {jump}")
       
                return [[1001]], jump, False, pop
            else:
                t0 = next_byte_end - Tf +10*108
                print("TIMEOUT - 3002")
                jump = int((t0-36)/9 + 1)
                print(f"Packet LOST - expected JUMP at ROW {jump}")
                return [[1001],[1002]], jump,False,  pop
        else:
            
            if np.max( processed_frame[jump:])==0:
                print("TIMEOUT - 2002")
                if plot and jump is not None:
                    plt.subplot(4,1,4)
                    plt.plot([jump,jump],[0,1],color = "red", linewidth = 3 )

                return [[1001]], None, False, False
            else:
                if close_miss_check and processed_frame[0]==1 :
                    print("TIMEOUT - 2003")
                    print("INFO : Accounted for close miss")
                    return [[1002],[1001]], None, False, False
                else:
                    if len(starts)>=2 and starts[-1]-starts[0]-durations[0]>110:
                        print("TIMEOUT - 2001")
                        return  [processed_frame[starts[0]+durations[0]:starts[-1]],[1001]], jump, False, False
                    else:
                        print("TIMEOUT - 2002")
                        return [[1001]], jump, False, False
    elif (time_out_index is not None) and len(markers_start)!=0:
        if time_out_index == 0 :
            print("VALID FRAME - 3003")
            packets.append([1001])
            if check_empty:
                pop = True
          
        else:
            add_timeout = True
            print("VALID FRAME - 4000")
            pass
    else:
        pass
    # Edge-Markers corrections
    if len(markers_start)>=1:
        if starts[0]==0 and durations[0]+200<markers_start[0] and (durations[0] not in markers_start):
            markers_start = [durations[0]]+markers_start
            s0 = 0
    elif len(markers_start)==0:
        try:
            if starts[0]==0 and durations[0]+200<starts[-1] :
                markers_start = [durations[0]]+markers_start
                s0 = 0
        except:
            pass
    # -------------------------------------------------------------
    # 2ND-Stage sequence seperation: END MARKERS
    for i, d in enumerate(durations):
        if d>=90 and d<100 and i>s0 and starts[i]-120>0:
            markers_end.append(starts[i])
    # Edge-Markers corrections
    for n,m in enumerate(markers_end):
        if m>markers_start[-1] and m -markers_start[-1]  <110:
            markers_end.pop(n)

    if len(markers_start)>1:
        if markers_start[-1]+120<864 and len(markers_start)!=len(markers_end) and markers_end[-1]!=starts[-1]:
            markers_end.append(starts[-1])
    else:
        if markers_start[-1]+120<864 and len(markers_end)==0:
            markers_end.append(starts[-1])

    
    # -------------------------------------------------------------
    
    # Checks for close miss on first packet
    if close_miss_check and markers_start[0]>30 :
        print("INFO : Accounted for close miss")
        packets.append([1002])


    try:
        if markers_end[-1]-markers_start[-1]> markers_end[-1] -markers_end[-2]:
            print("INFO : Popped END marker")
         
            markers_end.pop()   
    except:
        pass

    try:
        if -markers_start[0]+markers_start[1]< -markers_start[0] +markers_end[0]:
            print("INFO : Popped START marker")
          
            markers_start.pop(0)
    except:
        pass
    
    last_byte_time = 36 + 9*(markers_end[-1]-1)
    next_byte_start = last_byte_time + 10*108
    next_byte_end   = last_byte_time + 18*108


    
    # Markers iteration - extract packets
    i = 0
    while i<len(markers_end) :
        try:

            if markers_end[i]-markers_start[i]>110:
                    packets.append(processed_frame[markers_start[i]:markers_end[i]])
            else:
                #do nothing
                pass
        except:
            pass
        if plot:
            plt.subplot(4,1,4)
            try:
                plt.plot([markers_end[i], markers_end[i]],[0,1], color = "black", linestyle="--", linewidth =3)
                plt.plot([markers_start[i], markers_start[i]],[0,1], color = "green", linestyle="--", linewidth =3)
            except:
                pass
        i+=1
    # -------------------------------------------------------------

    if plot and jump is not None:
        plt.subplot(4,1,4)
        plt.plot([jump,jump],[0,1],color = "red", linewidth = 3 )

    # Packet Loss Check
    lost_packet = False
    if (next_byte_start>=Tf and next_byte_end>=Tf) : 
        t0 = next_byte_start - Tf
        jump = int((t0-36)/9 + 1)
        print(f"Packet JUMP - expected JUMP at ROW {jump}")
    elif (next_byte_start<Tf -Tg and next_byte_end<Tf -Tg  ):
   
        packets.append([1001])
        jump = None
        print("TIMEOUT  - Waiting for next message")
    else:
        t0 = next_byte_end - Tf +10*108
        jump = int((t0-36)/9 + 1)
        lost_packet = True
        if np.max(processed_frame[starts[-1]:])==0:
            check_empty = True
        else:
            check_empty = False
        print(f"Packet LOST - expected JUMP at ROW {jump}")
        packets.append([1002])
   # #if add_timeout:
    #    packets.append([1001])
    # ------------------------------------------------------------

    if lost_packet and plot:
            plt.subplot(4,1,4)
            plt.scatter(863,processed_frame[863],marker = "o", color = "red")
    return packets, jump, check_empty, pop
def compare_with(word, nsyn):
        dataTx = word.encode("utf-8")
        dataTx_bits = ''.join(format(byte, '08b') for byte in dataTx)
        rsc = RSCodec(nsyn)
        enc = rsc.encode(dataTx)
        dataTx_bits = ''.join(format(byte, '08b') for byte in enc)
        return dataTx_bits
def demodulate_OOK(data_packets, method = "GetData"):
    
    switch = True
    demodulated_data =[]
    demodulated_bitstream = []
    filtered_1001 = []
    prev = None
    for data in data_packets:
        if data[0] == 1001 and prev == 1001:
            continue
        filtered_1001.append(data)
        prev = data[0]
    data_packets = filtered_1001
    if method == "GetData":
    
        for data in data_packets:
      
            if data[0]==1001:
             
                if switch:
         
                    demodulated_bitstream.append(demodulated_data)
                    demodulated_data = []
                    switch = False
                else:
                    pass
            elif data[0]==1002:
                
                switch = True
                demodulated_data.append("XXXXXXXX")
            elif data[0]==1003:
               
                pass
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
    elif method == "Initiate":
        for data in data_packets:
            if data[0]!=1001 and data[0]!=1002 and data[0]!=1003:
                samples = np.array_split(data,10)
                demodulated_packet=""
                
                for i,s in enumerate(samples):
                    if i!=0 and i!=len(samples)-1:
                        s = list(s)
                        if s.count(0)>=s.count(1):
                            demodulated_packet+="0"
                        else:
                            demodulated_packet+="1"
                demodulated_bitstream.append(demodulated_packet)
    else:
        raise ValueError("Wrong input value: method = GetData or Initiate}")
    return demodulated_bitstream
def decode_ReedSolo(demodulated_bitstream):
    messages = [] # Stores the final messages
    total_err= []
    nsyn_nums= []
    errors = 0
    for index , stream in enumerate( demodulated_bitstream ):

        i = 0
        RSencoded = []  #RS encoded bytes - binary form
        erase_pos = []  #Marks the lost packets
        flag_nsyn = False
 
        if stream:
      
            for packet in stream:
                
                if i==0:
                    #FIRST PACKET
                    if packet =="XXXXXXXX":
                        #The first NSYN packet is missed
                        flag_nsyn = True
                        i+=1
                        continue
                    #The first NSYN packet is normally received
                    nsyn = int(packet,2)
                elif i==1 : 
                    #SECOND PACKET
                    if flag_nsyn:
  
                        #Since flag is raised, the second packet is the NSYN
                        nsyn = int(packet,2)
                    
                    else:
                        #Since flag is NOT raised, we check whether the second packet is a NSYN packet
                        if packet!="XXXXXXXX":
                            nsyn_2 = int(packet,2)
                            if nsyn_2!=nsyn:
                                #Not a NSYN packet
                                RSencoded.append(packet)
                            
                        else:
                            #NSYN packet, ignore
                            pass
                
                else:
                    # 3rd PACKET or ABOVE
                    if packet!= "XXXXXXXX":
                        RSencoded.append(packet)
                    else:
                        #mark erasure
                  
                        erase_pos.append(len(RSencoded))
                  
                        RSencoded.append("00000000")
                i+=1
            total_err.append(len(erase_pos))
            nsyn_nums.append(nsyn)
            rsc = RSCodec(nsyn) 
            enc_bytes = bytearray()
            for enc_byte in RSencoded:
                enc_bytes.append(int(enc_byte,2))
            try:
                #output = rsc.decode(enc_bytes, erase_pos=erase_pos)
                output = rsc.decode(enc_bytes)

                word = output[0].decode('utf-8', errors='ignore')
                messages.append(word)

            except reedsolo.ReedSolomonError as e:
                print("Error, during decoding... ")
                try:
                    erase_pos[-1]+=1
                
                    output = rsc.decode(enc_bytes, erase_pos=erase_pos)
          
                except reedsolo.ReedSolomonError as e:
                 
          
                
                    messages.append("Error 1004")

    return messages
def record_message(picam2,path=None):

    jump = None
    data_packets = []
    t0 = time.time()
    # Count the number of files in the folder - Initiate com

    folder_path = Path("/home/fotisber/Desktop/OCC_Laser/videos")
    num_files = len([f for f in folder_path.iterdir() if f.is_file()])    
    print("\033[31mCAMERA STATE: ACTIVE - WAITING FOR START SIGNAL\033[0m")
    print("")
    seq, time_start= videoRec.initiate_communication(picam2)
    t1 = time.time()
    # ---------------------------------------------------

    # Get INIT sequence
    cutoff_packet = False
    plot = False
    for f, s in enumerate(seq):
        
        processed_frame     = preprocess_frame(s, sigma=1, plot = plot)
        starts, durations   = calibrate_pulsewidth(processed_frame)
        packets, jump, pop, cutoff_packet= extract_packet_sequencies(processed_frame,starts, durations, plot ,jump,f, cutoff_packet)

        for n , p in enumerate(packets):
            data_packets.append(p)
    

    filtered_stream = demodulate_OOK(data_packets, method = "Initiate")
    # ---------------------------------------------------

    # Data length
    LS = filtered_stream[-1]
    MS = filtered_stream[0]
    total_bits_bin = MS+LS
    total_bits = int(total_bits_bin,2)
    print("Message length:  ",total_bits, f"({total_bits_bin})")
    # ---------------------------------------------------

    # Check for termination 
    if total_bits == 0:
        print("TERMINATION SEQUENCE: 0000 0000 0000 0000")
        return total_bits, None, None, None
    # ---------------------------------------------------
    
    t2 = time.time()
    Tproc = t2-time_start   # Camera processing time of the INIT seq 
    Tcap  = t1-t0           # Time until the initiation process is complete, until processing of INIT seq begins
    safe_padding = 0.15
    print("_"*60)
    print("Duration of Capturing Initiation     : ", np.round(Tcap*1e3),"ms")
    print("Processing Time of Initiation        : ", np.round(Tproc*1e3,2),"ms")
    print("Safe-Padding of Recording Duration   : ", np.round(safe_padding*1e3,2),"ms")
    print("_"*60)
    duration = total_bits*108*1e-6 + safe_padding
    
    if path is not None:
        video_duration = videoRec.capture_video(picam2,path = path,duration=duration)
        path_new = None
    else:
        path_new = f"videos/video{num_files}.mp4"
        video_duration = videoRec.capture_video(picam2,path = path_new,duration=duration)

    return total_bits, video_duration, Tproc, path_new
def get_stored_message(video_path,total_capture_time,method="File"  ):
    benchmarking = {"Frame Extraction":0, "Preprocessing":0, "Pulsewidth Calibration":0, "Packets Sampling":0, "Demodulation":0, "Decoding": 0}
    t0 = time.time()

    # Gets data frames from stored video file
    if method=="File":

        framesManager.EmptyFolder("/home/fotisber/Desktop/OCC_Laser/input_frames")
        frames, data_start_time, data_end_time, rec_duration = framesManager.FrameCapture(video_path)
        folder_path     = Path("/home/fotisber/Desktop/OCC_Laser/input_frames")
        # Count the number of files in the folder
        num_files   = len([f for f in folder_path.iterdir() if f.is_file()])    
        frames = []
        for f in range(num_files):

            frames.append(cv2.imread(f"input_frames/frame{f}.jpg"))

    elif method=="Array":

        frames, data_start_time, data_end_time, rec_duration = framesManager.GetFrames(video_path)
    else:

        raise ValueError("Invalid Input. Method can be either Array or File.")
    #---------------------------------------------------------------------------------

    # Demodulation and Decoding 

    data_packets = []
    jump = None 
    plot = True
    benchmarking["Frame Extraction"] = time.time()-t0
    check_empty = False
    for f, frame in enumerate(frames):
     
        t1 = time.time()
        processed_frame = preprocess_frame(frame,sigma=1, plot  = plot)
        benchmarking["Preprocessing"]+= time.time()-t1

        t2 = time.time()
        starts, durations = calibrate_pulsewidth(processed_frame)
        benchmarking["Pulsewidth Calibration"]+= time.time()-t2

        t3 = time.time()
        packets, jump, check_empty, pop= extract_packet_sequencies(processed_frame,starts, durations, jump, f, check_empty, plot)


        if pop and data_packets[-1][0]==1002 :
            print("TIMEOUT - 4001 : PACKET LOSS CORRECTION")
            data_packets.pop()

        for n , p in enumerate(packets):
            if plot:
                if len(data_packets)>1:
                    print(check_empty, pop, data_packets[-1][0])
                if len(p)<2:
                    print(p)
                else:
                    print("P")
            if p[0]!=1003:
                    data_packets.append(p)
            
        benchmarking["Packets Sampling"]+=time.time() -t3
        if plot:
            plt.show()
    
    t1  =   time.time( )
    demodulated_bitstream       = demodulate_OOK(data_packets)
    benchmarking["Demodulation"]=time.time()-t1

    t2  =   time.time()
    messages = decode_ReedSolo(demodulated_bitstream)
    benchmarking["Decoding"]    =time.time()-t2
    #---------------------------------------------------------------------------------
    total_bits = 0

    for i, m in enumerate(messages):
        dataTx      = m.encode("utf-8")
   
        dataTx_bits = ''.join(format(byte, '08b') for byte in dataTx)
        total_bits  +=len(dataTx_bits)
    
    Tproc   =   np.round(sum(list(benchmarking.values())[1:])*1e3,2)
    if total_capture_time==None:
        total_capture_time = rec_duration
    Ttot    =   np.round(sum(list(benchmarking.values()))*1e3 +total_capture_time*1e3, 3)
    R = np.round((total_bits/Ttot),3)
    print("")
    print("")
    print("|"+"_"*78+"|")
    print("{:<40}".format("\033[34mOptical Camera Communication System\033[0m"))
    print("{:<40} {:<40}".format("Modulation                :", "On-Off Keying (OOK)"))
    print("{:<40} {:<40}".format("Modulation Frequency      :", f"{str(np.round((1/108)*1e3,2))} kHz"))
    print("{:<40} {:<40}".format("FEC Algorithm             :", "Reed-Solomon"))
    print("_"*60)
    print("{:<40}".format("\033[31mCamera Specifications\033[0m"))
    print("{:<40} {:<40}".format("Camera Module:", "Raspberry Pi Camera Module 3 Wide"))
    print("{:<40} {:<40}".format("Frame Rate          :", "120  fps"))
    print("{:<40} {:<40}".format("Frame Duration      :", "8324 μs"))
    print("{:<40} {:<40}".format("Frame Gap Duration  :", "521  μs"))
    print("{:<40} {:<40}".format("Row Exposure Time   :", "36   μs"))
    print("{:<40} {:<40}".format("Row Readout Time    :", "9.02 μs"))
    print("|"+"_"*78+"|")
    print("")
    print("{:<15} {:<40}".format("Date & Time  :",str(datetime.now())))
    for i,m in enumerate(messages):
        if i==0:
            print("{:<5} {:<120}".format("\033[31mNo.  \033[0m", "\033[31mMessage\033[0m"))
        print("{:<5} {:<120}".format(i,m))
    print("_"*60)
    print("{:<30} {:<30}".format('Bits Received ', f"{np.round(total_bits/1e3,3)} kbit"))
    print("{:<30} {:<30}".format("Total Duration", f"{str(Ttot)} ms"))
    print("_"*60)
    fram_ext_dur = benchmarking["Frame Extraction"]
    print("{:<30}".format("\033[34mVideo Recording Information\33[0m"))
    print("{:<30} {:<30}".format("Video Path", video_path))
    print("{:<30} {:<30}".format("Video Recording Time", f"{np.round(total_capture_time*1e3)}       ms"))
    print("{:<30} {:<30}".format("Video Processing Time", f"{str(np.round(fram_ext_dur*1e3,2))}     ms"))
    print("{:<30} {:<30}".format("Message In-Video A.T.", f"{str(np.round(data_start_time*1e3,2))}  ms"))
    print("{:<30} {:<30}".format("Message In-Video E.T.", f"{str(np.round(data_end_time*1e3,2))}    ms"))
    print("_"*60)
    
    print("{:<30} {:<30}".format("Post-FEC Bit Rate ", f"{str(R)}   kbit/s"))
    print("{:<30} {:<30}".format("Bits Per Frame", f"{str(np.round((R/120)*1e3,2))} bits/frame"))
    print("_"*60)
    print("{:<30}".format("\033[34mSignal Processing Benchmarking\033[0m"))
    print("{:<30} {:<30}".format("Signal Processing Time", f"{str(Tproc)} ms"))
    print("-"*60)
    print("{:<30} {:<30}".format('Process', 'Duration (μs)'))
    print("-"*60)
    for proc, dur in benchmarking.items():
        dur = int(np.round(dur*1e6))
        if proc == "Frame Extraction":
            continue
        print("{:<30} {:<30}".format(proc, str(dur)))
    print("|"+"_"*78+"|")
if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    
    filename = input("Type the filename of the .mp4 captured video, or press ENTER to capture a new video : ")
    if filename!="":
        t0 = time.time()
        path = "videos/"+filename+".mp4"
        message = get_stored_message(path,total_capture_time=None, method="Array")
    else:
        filename = input("Type the filename of your NEW .mp4 captured video, OR press ENTER to \nESTABLISH communication SEQUENCE : ")
        if filename!="":
            path = "videos/"+filename+".mp4"
            picam2, config = videoRec.start_camera()
      
            total_bits, video_duration,Tproc, path_new = record_message(picam2,path)
            total_capture_time = video_duration + Tproc
            picam2.close()
            get_stored_message(path,  total_capture_time,method = "Array")
        else:
            
            print("Entered communication sequence mode.")
            print("-"*60)
            while(1):
                picam2, config = videoRec.start_camera()

                total_bits, video_duration,Tproc,path_new = record_message(picam2 )
                total_capture_time = video_duration + Tproc
                if total_bits==0:
                    print("")
                    print("_-*30")
                    print("")
                    print("\033[32mCONNECTION TERMINATED BY SENDER\033[0m")
                    print("")
                    print("_-*30")
                    picam2.close()
                    break
                get_stored_message(path_new, total_capture_time ,method = "Array")
                picam2.close()
            try:
                picam2.close()
            except:
                pass
          
                
