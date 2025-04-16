from picamera2 import Picamera2
import time
import numpy as np
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

def capture_data(path):
    hour = int(time.strftime('%H'))
    now = time.strftime("%y_%m_%d_%H_%M")

    mp4_output = path

    picam2 = Picamera2()
    #print(picam2.sensor_modes)
    mode = picam2.sensor_modes
    # Configure the camera with specific settings
    # Set resolution (e.g., 1920x1080)

    config = picam2.create_video_configuration(main={"size": (16, 864)} , controls ={
        'ExposureTime': 36,  # Set exposure time in microseconds (e.g., 10ms)
        'AeFlickerPeriod' : 108 ,
        'FrameRate' :150,
        'AeEnable': False,
        'AnalogueGain' : 1,
        'AwbEnable': False ,     # Turn off Auto White Balance,
        'LensPosition' :32}, buffer_count= 8, sensor ={'output_size':(1536,864), 'bit_depth' :8 })
    picam2.configure(config)


    encoder = H264Encoder(bitrate=2000000)
    output = FfmpegOutput(mp4_output)
    x = input("Press Any Button")
    picam2.start_recording(encoder, output)

    print(True)
    time.sleep(3)
    x = picam2.capture_metadata()
    picam2.stop_recording()
    # Record for 10 seconds (you can change the duration as needed)
    print(x)
    # Stop the recording and release the camera
    picam2.close()
if __name__ =="__main__":
    path = "videos/videofeed_test.mp4"
    capture_data(path)