import cv2 
import numpy as np 
import os
import shutil
# Function to extract frames 
def FrameCapture(folder_path): 

	# Path to video file 
	vidObj = cv2.VideoCapture(folder_path) 

	# Used as counter variable 
	count = 0

	# checks whether frames were extracted 
	success = True

	while success:
		success, frame = vidObj.read()
		if success:
			r , g, b = cv2.split(frame)
			if np.amax(r)>5:
				path2 = "input_frames/frame"+str(count)+".jpg"
				cv2.imwrite(path2,frame)
				count = count+1
	print(f"Extracted {count} frames.")
def EmptyFolder(folder_path):
	for filename in os.listdir(folder_path):
		file_path = os.path.join(folder_path, filename)
		try:
			if os.path.isfile(file_path) or os.path.islink(file_path):
				os.unlink(file_path)
			elif os.path.isdir(file_path):
				shutil.rmtree(file_path)
		except Exception as e:
			print(f"Failed to Delete:{e}")
# Driver Code 
if __name__ == '__main__': 

	EmptyFolder("/home/fotisber/Desktop/OCC_Laser/input_frames")
 
	FrameCapture("videos/videofeed_CheckLydia.mp4")