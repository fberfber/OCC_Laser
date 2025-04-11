# Program To Read video 
# and Extract Frames 

import cv2 
import numpy as np 
# Function to extract frames 
def FrameCapture(path): 

	# Path to video file 
	vidObj = cv2.VideoCapture(path) 

	# Used as counter variable 
	count = 0

	# checks whether frames were extracted 
	success = True

	while success:
		success, frame = vidObj.read()
		if success:
			r , g, b = cv2.split(frame)
			if np.amax(r)>20:
				path2 = "/home/fberfber/Desktop/app/final/zeroencoding/frame"+str(count)+".png"
				cv2.imwrite(path2,frame)
				count = count+1
				print(count)


# Driver Code 
if __name__ == '__main__': 

	# Calling the function 
    FrameCapture("/home/fberfber/Desktop/app/final/zeroencoding/onoff0.010751814202947019.mp4")