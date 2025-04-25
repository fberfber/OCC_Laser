from picamera2 import Picamera2
import time
import numpy as np
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from matplotlib import pyplot as plt
import logging
def start_camera():
    picam2 = Picamera2()
    config_vid = picam2.create_video_configuration(main={"size": (16, 864), "format":"RGB888"} , controls ={
        'ExposureTime': 36,  # Set exposure time in microseconds (e.g., 10ms)
        'AeFlickerPeriod' : 108 ,
        'FrameRate' :150,
        'AeEnable': False,
        'AnalogueGain' : 1,
        'AwbEnable': False ,     # Turn off Auto White Balance,
        'LensPosition' :32}, buffer_count= 8, sensor ={'output_size':(1536,864), 'bit_depth' :8 })
    picam2.configure(config_vid)
    picam2.start()
    time.sleep(0.1)
    return picam2, config_vid
def initiate_communication(picam2,plot=False ):
    signal = 0
    flag = True
    sequence = []
    start_flag = False
    end_flag    = False
    t0 = time.time()
    time_start = 0
    c = 0
    backround = 0
    while 1:
        t1 = time.time()

        frame = picam2.capture_array("main")
        signal = np.max(frame)
        if c <10:
            backround +=signal
        elif c==10:
            thres = backround/10 +10
        else:
            if signal>thres and flag:
                print("SIGNAL       detected            ----- ")
                flag = False
            elif signal<10 and (not flag) and not(start_flag):
                print("WAITING      for message length  ----- ")
                start_flag = True
            elif start_flag and signal>thres:
                #print("PROCESSING   message length      ----- ", t1-t0)
                end_flag    = True
                sequence.append(frame.astype(np.int32))
            elif end_flag and signal<thres:
                flag = True
                start_flag = False
                end_flag = False
                
                print("RECORDING    message             ----- ")
                time_start = time.time()
                break
            elif t1-t0>20:
                raise RuntimeError("Connection TIME-OUT.  ")
            elif flag:
                if c%20==0:
                    print("WAITING for message - Timeout in ...", f"\033[31m{np.round( 20 -(time.time()-t0),2)} seconds\033[0m")
                
            else: 
                
                pass
        c+=1
    
    if plot:
        plt.figure()
        for i,s in enumerate(sequence):
            s = np.mean(s[:,:,2],axis=1)
            plt.subplot(1,len(sequence),i+1)
            plt.plot(s)
        plt.show()
    return sequence, time_start
def capture_video(picam2,path, duration):
    t0  = time.time()
    mp4_output  = path
    encoder     = H264Encoder(bitrate=2000000)
    output      = FfmpegOutput(mp4_output)


    duration_of_init = np.round((time.time()-t0)*1e3,2)
    picam2.start_recording(encoder, output)
        
    print("\033[31mCAMERA STATE: ACTIVE - RECORDING DATA\033[0m")
   
    print("")
    print("-"*60)
    print("Recording was initiated after : ",duration_of_init , " ms")
    print("Recording Duration            : ",duration_of_init+duration," ms")

    time.sleep(duration)
    #x = picam2.capture_metadata()
    picam2.stop_recording()
    print("-"*60)
    print("\033[31mCAMERA STATE: OFF    - RECORDING COMPLETED\033[0m")
    print("-"*60)
    return duration 

    
if __name__ =="__main__":
    logging.getLogger("Picamera2").setLevel(logging.ERROR)
    picam2 = start_camera()

    x = input("Press Any Button - Initiate")
    seq = initiate_communication(picam2,True)
    picam2.close()
    path = "videos/videofeed.mp4"
    #capture_data(path)
