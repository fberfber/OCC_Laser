import cv2 
import numpy as np 
import os
import shutil
# Function to extract frames 
def FrameCapture(folder_path): 

	# Path to video file 
	vidObj 	= cv2.VideoCapture(folder_path) 

	# Used as counter variable 
	count 	= 0

	# checks whether frames were extracted 
	success 	= True
	skip 	= False
	data_start_counter 	= 0
	data_start_time 	= 0
	data_end_time 		= 0 
	while success:

		success, frame = vidObj.read()
		if success:

			r , g, b = cv2.split(frame)
			if np.amax(r)>5:
				if data_start_time==0:
					data_start_time =data_start_counter
				data_end_time = data_start_counter
				path2	= "input_frames/frame"+str(count)+".jpg"
				cv2.imwrite(path2,frame)
				count	= count+1
				skip	= False
			else:
				if skip:

					pass
				else:

					path2	= "input_frames/frame"+str(count)+".jpg"
					cv2.imwrite(path2,frame)
					skip	= True
			data_start_counter+=0.008324
	print(f"Extracted {count} frames.")
	return data_start_time, data_end_time
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
def GetFrames(folder_path):
	vidObj = cv2.VideoCapture(folder_path) 
	frames = []
	# Used as counter variable 
	count = 0

	# checks whether frames were extracted 
	success = True
	averages = [] 
	skip = False
	data_start_time		= 0
	data_counter		= 0
	data_end_time	= 0 
	while success:
		success, frame = vidObj.read()
		if success:
			r , _, _ = cv2.split(frame)
			if np.amax(r)>5:
				if data_start_time==0:
			
					data_start_time =data_counter
				frames.append(frame)
			
				data_end_time = data_counter
				count = count+1
				skip = False
			else:
				if skip:
					
					pass
				else:
					
					frames.append(frame)
					skip = True
			
			data_counter+=0.008324
	rec_duration = data_counter
	print(f"Extracted {count} frames.")
	return frames, data_start_time, data_end_time, rec_duration
# Driver Code 
if __name__ == '__main__': 

	EmptyFolder("/home/fotisber/Desktop/OCC_Laser/input_frames")
 
	FrameCapture("videos/videofeed.mp4")
