import Pyro4
import os 
import cv2
import time
import threading
import pickle
MAX_FILE_SIZE=300000000

@Pyro4.expose
class EdgeMonitoringDevice():

	#This is the constructor of the EdgeMonitoringDevice class
	def __init__(self,camera_path,output_file):
		self.threadServer = 0
		self.camera_path=camera_path
		self.output_file=output_file
		self.write_semaphore=threading.Semaphore(0)
		self.read_semaphore=threading.Semaphore(0)
		self.lock=threading.Lock()
		self.destroy_flag=0
		self.vid=cv2.VideoCapture(output_file)

	def capture_function(self):
		global MAX_FILE_SIZE
		
		print(self.camera_path)
		print(self.output_file)
		
		#Create a VideoCapture object
		#For example, camera_path is "/dev/v4l/by-id/usb-AONI_ELECTRONIC_CO.LTD_Canyon_CNS-CWC5_Webcam_20190322001-video-index0"
		#If a device has only one camera, we can use 0 as a camera_Path
		cap = cv2.VideoCapture(self.camera_path)

		# Check if camera opened successfully
		if (cap.isOpened() == False): 
			print("Unable to read camera feed")
			return -1
		
		frame_width = int(cap.get(3))
		frame_height = int(cap.get(4))

		while(True):
			
			#Wait here until the fetch_data method is called
			self.write_semaphore.acquire()
			
			self.lock.acquire()
			#If destroy_flag is 1, then close the out instance and also close the camera
			if(self.destroy_flag==1):
				print("DESTROY THREAD")
				out.release()
				cap.release()
				self.lock.release()
				return()
			self.lock.release()
			
			#Read a frame from the camera
			ret, frame = cap.read()
			
			#Open the self.output_file file and write the frame into it
			fd = os.open(self.output_file, os.O_RDWR|os.O_CREAT|os.O_TRUNC)
			os.close(fd)
			# Define the codec and create VideoWriter object.The output is stored in the self.output_file file.
			out = cv2.VideoWriter(self.output_file,cv2.VideoWriter_fourcc('M','J','P','G'), 20, (frame_width,frame_height))
			out.write(frame)
			out.release()
			#Release the read semaphore in order to wake up the fetch_data
			self.read_semaphore.release()
			
	#This is the first method called by the proxy
	def start_capture(self):
		
		#When the proxy calls this function, a thread is created in order to open the camera and to start the video capture
		self.threadServer = threading.Thread(target=self.capture_function, args=())
		self.threadServer.start()
		return
	
	#This function is called again and again by the proxy
	def fetch_data(self):
		global MAX_FILE_SIZE
		
		#Release the write semaphore in order to wake up the capture_function
		self.write_semaphore.release()
		#Wait here until the capture_function method read the frame
		self.read_semaphore.acquire()
		
		array = bytes() 
		fd = os.open(self.output_file,os.O_RDONLY)
		BLOCK_SIZE=1024
		
		try:
			#Try to read 500 Blocks of data
			data=os.read(fd,500*BLOCK_SIZE)
			array+=data
			os.close(fd)
			
			#Return the raw data (bytes) to the proxy
			return(array)
			
		except IOError:
			print("Error during reading")
			os.close(fd)
	
	#This function is called from the proxy in order to inform the skeleton that the proxy object will not exist anymore
	def end_capture(self):
		print("Close capture device")
		
		self.lock.acquire()
		#Set the destroy_flag to 1. The thread will see this flag and it will terminate
		self.destroy_flag=1
		self.lock.release()
		self.write_semaphore.release()
		print("Wait for my thread to terminate")
		#Wait for the thread to terminate
		self.threadServer.join()
		print("My thread returned")
		return()
		
			
		

