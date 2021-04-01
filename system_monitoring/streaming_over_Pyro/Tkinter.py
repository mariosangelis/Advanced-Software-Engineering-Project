from tkinter import *
from PIL import ImageTk, Image
import time
from tkinter import messagebox
import threading
import Pyro4
import PIL.Image, PIL.ImageTk
import os
import cv2
import base64
import serpent
import socket
import numpy as np
import sys
import pickle
from pyshortcuts import make_shortcut

lock = threading.Lock()
destroy_flag,cap,duplicates,net,ObjectDetection,record=0,0,0,0,0,0
ip_camera_list=[]
ip_out=[]
MAX_FILE_SIZE=50000000
CREATE_NEW_OBJECTS_TYPE=1
DELETE_OBJECTS_TYPE=2
MAX_LIST_SIZE=3000
CLASSES=[]
COLORS=[]
        
#The destroy function will be called when the close button is pressed
def _destroy(event):
	global lock
	global destroy_flag
	
	lock.acquire()
	
	#Set delete_flag to 1
	if(destroy_flag==0):
		destroy_flag=1
	lock.release()
	
#Each edge device has a stream object
class stream_class:
	def __init__(self):
		self.stream_list=[]
		self.write_position=0
		self.mtx=threading.Lock()
		
	#Return a list which contains all the captured frames
	def get_stream_list(self):
		return self.stream_list
	
	#Reset the frame list
	def reset_list(self):
		self.stream_list=[]
	
	#Return the write descriptor's position
	def get_write_position(self):
		return self.write_position
		
	#Set the write descriptor's position
	def set_write_position(self,pos):
		self.write_position=pos
	
	#Release the mutex
	def release(self):
		self.mtx.release()
	
	#Acquire the mutex
	def acquire(self):
		self.mtx.acquire()
	
	#Add the frame called img to the end of the stream list
	def add_to_list(self,frame):
		global MAX_LIST_SIZE
		
		self.stream_list.insert(self.write_position,frame)
		self.write_position+=1
		
class App:
	#This is the constructor of the class
	def __init__(self, window, window_title,EdgeMonitoringDevice_list):
		global cap
		global record
		self.panel_list=[]
		self.thread_list=[]
		self.vid_list=[]
		self.remote_out=[]
		
		#Create N threads
		#Each one represents a camera service
		#Each thread will fetch the data from the server side and it will save it into the file specified by the last argument (ex: video1.avi for the first thread)
		
		for i in range(0,len(EdgeMonitoringDevice_list)):
			if record==1:
				name="records/remote_camera"+str(i)+"_record.avi"
				self.remote_out.append(cv2.VideoWriter(name,cv2.VideoWriter_fourcc('M','J','P','G'), 20, (900,500)))
				
			self.vid_list.append(stream_class())
			self.thread_list.append(threading.Thread(target=self.thread_function, args=[EdgeMonitoringDevice_list[i],self.vid_list[-1]]))
		
		for i in range(0,len(self.thread_list)):
			self.thread_list[i].start()
		
		
		self.window = window
		self.window.title("Wireless Box Surveillance System")
		self.window.geometry("1800x1000")
		self.window.configure(background='black')
		self.window.resizable(0,0)

		iconpath="logo.png"
		iconimg = ImageTk.PhotoImage(Image.open(iconpath))
		self.window.iconphoto(False, iconimg)
		
		#The Label widget is a standard Tkinter widget used to display a text or image on the screen.
		img = ImageTk.PhotoImage(Image.open("6.jpg"))  
		self.panel_list.append(Label(self.window,image=img,height=500,width=900,highlightbackground="black",highlightthickness=1))
		self.panel_list[0].configure(background='black')
		self.panel_list[0].grid(row=0,column=0)
		
		self.panel_list.append(Label(self.window,image=img,height=500,width=900,highlightbackground="black",highlightthickness=1))
		self.panel_list[1].grid(row=0,column=1)
		self.panel_list[1].configure(background='black')
		
		self.panel_list.append(Label(self.window,image=img,height=500,width=900,highlightbackground="black",highlightthickness=1))
		self.panel_list[2].grid(row=1,column=0)
		self.panel_list[2].configure(background='black')
		 
		self.panel_list.append(Label(self.window,image=img,height=500,width=900,highlightbackground="black",highlightthickness=1))
		self.panel_list[3].grid(row=1,column=1)
		self.panel_list[3].configure(background='black')
		
		
		#Wait for caching purposes
		time.sleep(2)
		
		self.update()
		#The destroy function will be called when the close button is pressed 
		self.window.bind("<Destroy>", _destroy)
		self.window.mainloop()
	
	#Each camera service has a thread
	def thread_function(self,EdgeMonitoringDevice,vid):
		global destroy_flag
		global lock
		global MAX_LIST_SIZE
	
		while(True):
			#Each thread, inside a while loop, will trying to fetch data from the skeleton by calling the fetch_data method
				
			lock.acquire()
			#If destroy_flag is 1, then close the writing file descriptor and call the end_capture method in order to inform the skeleton that this proxy will not exist anymore
			if(destroy_flag==1):
				print("DESTROY THREAD")
				EdgeMonitoringDevice.end_capture()
				lock.release()
				return()
			lock.release()
			
			#Fetch raw data from the server side, using Pyro4
			array=EdgeMonitoringDevice.fetch_data()
			data = serpent.tobytes(array)
			
			#Add the raw data to the stream list
			vid.acquire()
			vid.add_to_list(data)
			#print(self.vid1.get_write_position())
			
			#Write decriptor has finished, reset the write descriptor and reset the stream list
			if(len(vid.get_stream_list())==MAX_LIST_SIZE):
				vid.set_write_position(0)
				vid.reset_list()
				
			vid.release()
	
	#Object detection model function
	def detection_service(self,frame):
		global net
		global CLASSES
		global COLORS
		
		(h, w) = frame.shape[:2]
		blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),0.007843, (300, 300), 127.5)
		# pass the blob through the network and obtain the detections and
		# predictions
		net.setInput(blob)
		detections = net.forward()
		# loop over the detections
		for i in np.arange(0, detections.shape[2]):
			# extract the confidence (i.e., probability) associated with
			# the prediction
			confidence = detections[0, 0, i, 2]
			# filter out weak detections by ensuring the `confidence` is
			# greater than the minimum confidence
			if confidence > 0.2:
				# extract the index of the class label from the
				# `detections`, then compute the (x, y)-coordinates of
				# the bounding box for the object
				idx = int(detections[0, 0, i, 1])
				box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
				(startX, startY, endX, endY) = box.astype("int")
				# draw the prediction on the frame
				label = "{}: {:.2f}%".format(CLASSES[idx],confidence * 100)
				cv2.rectangle(frame, (startX, startY), (endX, endY),COLORS[idx], 2)
				y = startY - 15 if startY - 15 > 15 else startY + 15
				cv2.putText(frame, label, (startX, y),cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
		
	#The update method will be automatically called every "delay" milliseconds, 50 in our case
	def update(self):
		global lock
		global cap
		global duplicates
		global ObjectDetection
		global record
		global ip_camera_list
		global ip_out
		
		for i in range(0,len(ip_camera_list)):
			#Read a frame from the IP camera
			#------------------------------------------------------------------------------------#
			ret, frame = ip_camera_list[i].read()
			if ret:
				frame=cv2.resize(frame, (900, 500))
				
				if record==1:
					ip_out[i].write(frame)
				
				#Apply the object detection model
				if(ObjectDetection==1):
					self.detection_service(frame)
				
				#Apply the image generated from the current frame to the specific panel
				cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA
				self.photo = Image.fromarray(cv2image)              # convert image for PIL
				imgtk = ImageTk.PhotoImage(image=self.photo)        # convert image for tkinter 
				self.panel_list[i].imgtk = imgtk                    # anchor imgtk so it does not be deleted by garbage-collector  
				self.panel_list[i].config(image=imgtk)              # show the image
			#------------------------------------------------------------------------------------#
		
		
		for i in range(0,len(self.vid_list)):
		
			#Read a frame from the video stream
			#------------------------------------------------------------------------------------#
			self.vid_list[i].acquire()
			if(len(self.vid_list[i].get_stream_list())>0):
				try:
					#Get the last frame from the frame list
					data=self.vid_list[i].get_stream_list()[-1]
					
					#Write the raw data in a file and read them again as a frame using VideoCapture
					fd = os.open("write_file.avi", os.O_RDWR|os.O_CREAT|os.O_TRUNC)
					os.write(fd,data)
					os.close(fd)
					
					vid=cv2.VideoCapture("write_file.avi")
					ret,frame=vid.read()
					if ret:
						
						frame=cv2.resize(frame,(900,500))
						if record==1:
							self.remote_out[i].write(frame)
						#Apply the object detection model
						if(ObjectDetection==1):
							self.detection_service(frame)
						cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)                           # convert colors from BGR to RGBA
						self.photo = Image.fromarray(cv2image)                                       # convert image for PIL
						imgtk = ImageTk.PhotoImage(image=self.photo)                                 # convert image for tkinter 
						self.panel_list[len(ip_camera_list)+i].imgtk = imgtk                         # anchor imgtk so it does not be deleted by garbage-collector  
						self.panel_list[len(ip_camera_list)+i].config(image=imgtk)                   # show the image
				except Exception as e:
					print("exception")
					
			self.vid_list[i].release()
		#------------------------------------------------------------------------------------#
		

		self.window.after(30, self.update)
 
def main(remote_devices_list,ip_devices_list,ObjectDetectionFlag,recordFlag):
	global CREATE_NEW_OBJECTS_TYPE
	global DELETE_OBJECTS_TYPE
	global cap
	global net
	global CLASSES
	global COLORS
	global ObjectDetection
	global record
	global ip_camera_list
	global ip_out
	
	EdgeMonitoringDevice_list=[]
	ip_camera_list=[]
	ObjectDetection=ObjectDetectionFlag
	record=recordFlag
	
	#This is the object detection model initialization
	#--------------------------------------------------------------------------------#
	if(ObjectDetection==1):
		CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
		"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
		"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
		"sofa", "train", "tvmonitor"]
		COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))


		# load the serialized model from disk
		print("[INFO] loading model...")
		net = cv2.dnn.readNetFromCaffe("MobileNetSSD_deploy.prototxt","MobileNetSSD_deploy.caffemodel")
	#--------------------------------------------------------------------------------#
	
	if record==1:
		for i in range(0,len(remote_devices_list)):
			name="records/remote_camera"+str(i)+"_record.avi"
			fd = os.open(name, os.O_RDWR|os.O_CREAT|os.O_TRUNC)
			os.close(fd)
		for i in range(0,len(ip_devices_list)):
			name="records/ip_camera"+str(i)+"_record.avi"
			fd = os.open(name, os.O_RDWR|os.O_CREAT|os.O_TRUNC)
			os.close(fd)
			ip_out.append(cv2.VideoWriter(name,cv2.VideoWriter_fourcc('M','J','P','G'), 20, (900,500)))
	
	for i in range(0,len(remote_devices_list)):
		
		#Create a tcp socket in order to get the Pyro ids from the server
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		#Connect to the edge device
		#-------------------------------------------------------------------------------#
		server_address = (remote_devices_list[i][0],remote_devices_list[i][1])
		sock.connect(server_address)
		
		#Send a CREATE_NEW_OBJECTS_TYPE type message in order to receive the pyro id from the server
		#message = [CREATE_NEW_OBJECTS_TYPE,"/dev/v4l/by-id/usb-046d_0825_5BBAE2E0-video-index0"]
		message = [CREATE_NEW_OBJECTS_TYPE,0]
		message=pickle.dumps(message)
		sock.sendall(message)
		
		object_id = sock.recv(10000)
		object_id=pickle.loads(object_id)
		#Data contains the pyro id
		print(object_id[0])
		sock.close()
		
		#Create the proxy object
		EdgeMonitoringDevice_list.append(Pyro4.Proxy(object_id[0]))
		#Call start capture function. The skeleton will open the camera and will capture the video
		EdgeMonitoringDevice_list[i].start_capture()
		#-------------------------------------------------------------------------------#
	
	for i in range(0,len(ip_devices_list)):
		#connect with the IP camera
		#-------------------------------------------------------------------------------#
		ip_camera_list.append(cv2.VideoCapture("rtsp://admin:camera1@"+ip_devices_list[i]+":555//h264Preview_01_sub"))
		if (ip_camera_list[-1].isOpened() == False): 
			print("Unable to read camera feed")
		#-------------------------------------------------------------------------------#
	
	#Create an object of the App class. Pass the Pyro proxies as arguments
	obj=App(Tk(),"Tkinter and OpenCV",EdgeMonitoringDevice_list)
	
	print("Waiting threads to return")
	#Wait for the threads to return
	for i in range(0,len(obj.thread_list)):
		obj.thread_list[i].join()
		print("Thread ",i," returned")
		
	
	if record==1:
		for i in range(0,len(remote_devices_list)):
			obj.remote_out[i].release()
		
		for i in range(0,len(ip_devices_list)):
			ip_out[i].release()
	
	for i in range(0,len(remote_devices_list)):
		#Create a tcp socket in order to inform the server side that the proxies will not exist anymore
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address = (remote_devices_list[i][0],remote_devices_list[i][1])
		sock.connect(server_address)
		
		#Send a DELETE_OBJECTS_TYPE type message in order to inform the server side that the proxies will not exist anymore
		message = [DELETE_OBJECTS_TYPE]
		message=pickle.dumps(message)
		sock.sendall(message)
		sock.close()

if __name__=="__main__":
    

	if(sys.argv[1]=="--help"):
		print("python3 Tkinter.py --remote_camera <ip1> <p1> <ip2> <p2> ... --ip_camera <ip1> <ip2> ... --object_detection 0 --record 0")
		print("--remote_camera    [Specifies the ip and port combination for each remote device]")
		print("--ip_camera        [Specifies the ip address for each ip camera]")
		print("--object_detection [Specifies if the object detection service is enabled or disabled]")
		print("--record           [Specifies if the user wants to record each camera's stream]")
		exit()
		
	if(len(sys.argv)<5):
		print("Wrong number of arguments. Please give the arguments as in the following format")
		print("python3 Tkinter.py --remote_camera <ip1> <p1> <ip2> <p2> ... --ip_camera <ip1> <ip2> ... --object_detection 0 --record 0")
		exit()
		
	remote_devices_list=[]
	ip_devices_list=[]
	
	for i in range(1,len(sys.argv)):
		if sys.argv[i]=="--remote_camera":
			j=i+1
			while(j < len(sys.argv)):
				if sys.argv[j][0]=="-":
					break
				remote_devices_list.append([sys.argv[j],int(sys.argv[j+1])])
				j+=2
		elif sys.argv[i]=="--ip_camera":
			for j in range(i+1,len(sys.argv)):
				if sys.argv[j][0]=="-":
					break
				ip_devices_list.append(sys.argv[j])
		elif sys.argv[i]=="--object_detection":
			ObjectDetection=int(sys.argv[i+1])
		elif sys.argv[i]=="--record":
			record=int(sys.argv[i+1])
			break
	
	#print(remote_devices_list)
	#print(ip_devices_list)
	main(remote_devices_list,ip_devices_list,ObjectDetection,record)


