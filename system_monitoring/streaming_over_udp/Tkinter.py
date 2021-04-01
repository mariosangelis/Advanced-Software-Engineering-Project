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
import struct

lock = threading.Lock()
destroy_flag,cap,duplicates,ObjectDetection=0,0,0,0
MAX_LIST_SIZE=3000
CREATE_NEW_OBJECTS_TYPE=1
DELETE_OBJECTS_TYPE=2
POLL_UDP_STREAM_SOCKET=3
CLASSES=[]
COLORS=[]
stream_port=30000
MAX_DGRAM = 2**16

#Empty socket's buffer
def dump_buffer(s):
	global MAX_DGRAM
	
	while True:
		seg, addr = s.recvfrom(MAX_DGRAM)
		if struct.unpack("B", seg[0:1])[0] == 1:
			print("Finish emptying buffer")
			break
	
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
		self.read_position=0
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
	def add_to_list(self,img):
		global MAX_LIST_SIZE
		
		self.stream_list.insert(self.write_position,img)
		self.write_position+=1
	
class App:
	#This is the constructor of the class
	def __init__(self, window, window_title,EdgeMonitoringDevice):
		global cap
		#Create N threads
		#Each one represents a camera service
		#Each trhread will fetch the data from the server side and it will save the data into the file specified by the last argument (ex: video1.avi for the first thread)
		self.thread1 = threading.Thread(target=self.thread_function, args=[EdgeMonitoringDevice,"video1.avi"])
		
		#Start the threads
		self.thread1.start()
		
		self.window = window
		self.window.title("Surveillance system")
		self.window.geometry("1800x1000")
		self.window.configure(background='black')
		self.window.resizable(0,0)

		iconpath="icon.png"
		iconimg = ImageTk.PhotoImage(Image.open(iconpath))
		self.window.iconphoto(False, iconimg)

		#The Label widget is a standard Tkinter widget used to display a text or image on the screen.
		img = ImageTk.PhotoImage(Image.open("6.jpg"))  
		self.panel1 = Label(self.window,image=img,height=500,width=900,highlightbackground="black",highlightthickness=1)
		self.panel1.configure(background='black')
		self.panel1.grid(row=0,column=0)
		
		img2 = ImageTk.PhotoImage(Image.open("6.jpg"))  
		self.panel2 = Label(self.window,image=img2,height=500,width=900,highlightbackground="black",highlightthickness=1)
		self.panel2.grid(row=0,column=1)
		self.panel2.configure(background='black')
		
		img3 = ImageTk.PhotoImage(Image.open("6.jpg"))  
		self.panel3 = Label(self.window,image=img3,height=500,width=900,highlightbackground="black",highlightthickness=1)
		self.panel3.grid(row=1,column=0)
		self.panel3.configure(background='black')
		
		img4 = ImageTk.PhotoImage(Image.open("6.jpg"))  
		self.panel4 = Label(self.window,image=img4,height=500,width=900,highlightbackground="black",highlightthickness=1)
		self.panel4.grid(row=1,column=1)
		self.panel4.configure(background='black')
		
		#Each edge device has a stream object which contains the steram list and the write descriptor
		self.vid1=stream_class()
		
		#Wait for caching purposes
		time.sleep(10)
		
		self.update()
		#The destroy function will be called when the close button is pressed 
		self.window.bind("<Destroy>", _destroy)
		self.window.mainloop()
	
	#Each camera service has a thread
	def thread_function(self,EdgeMonitoringDevice,video_file):
		
		global destroy_flag
		global lock
		global stream_port
		global MAX_DGRAM
		global POLL_UDP_STREAM_SOCKET
		global MAX_LIST_SIZE

		#Open the video file and set the file descriptor to the end of the file
		fd1 = os.open(video_file, os.O_RDWR|os.O_CREAT)
		os.lseek(fd1,0,os.SEEK_END)
		#Create a udp socket in order to get the udp stream
		udp_stream_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		server_address = (EdgeMonitoringDevice.get_wan_ip(),stream_port)
		print("Server address is ",server_address)
		
		#Send a poll message to the server side
		poll=pickle.dumps(POLL_UDP_STREAM_SOCKET)
		time.sleep(4)
		print("Send POLL_UDP_STREAM_SOCKET")
		udp_stream_socket.sendto(poll,server_address)
		
		#Initialize current_frame
		current_frame = b''
		dump_buffer(udp_stream_socket)
		
		while True:
			#Receive a part of the total frame
			frame_part, addr = udp_stream_socket.recvfrom(MAX_DGRAM)
			
			#This is an intermediate part of the frame
			if struct.unpack("B", frame_part[0:1])[0] > 1:
				current_frame += frame_part[1:]
			#This is the last part of the frame
			else:
				lock.acquire()
				#If destroy_flag is 1, then close the writing file descriptor and call the end_capture method in order to inform the skeleton that this proxy will not exist anymore
				if(destroy_flag==1):
					print("DESTROY THREAD")
					EdgeMonitoringDevice.end_capture()
					lock.release()
					return()
				lock.release()
				
				current_frame += frame_part[1:]
				
				img = cv2.imdecode(np.fromstring(current_frame, dtype=np.uint8), 1)
				#print(self.vid1.get_write_position())
				
				#Add the frame to the stream list
				self.vid1.acquire()
				self.vid1.add_to_list(img)
				
				#Write decriptor has finished, reset the write descriptor and reset the stream list
				if(len(self.vid1.get_stream_list())==MAX_LIST_SIZE):
					self.vid1.set_write_position(0)
					self.vid1.reset_list()
					
				self.vid1.release()
				
				#cv2.imshow('frame', img)
				#if cv2.waitKey(1) & 0xFF == ord('q'):
				#	break
				current_frame = b''

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
				
	#The update method will be automatically called every "delay" milliseconds
	def update(self):
		global lock
		global cap
		global ObjectDetection
		
		#Read a frame from the video stream
		#------------------------------------------------------------------------------------#
		self.vid1.acquire()
		if(len(self.vid1.get_stream_list())>0):
			try:
				#Get the last frame from the frame list
				img=self.vid1.get_stream_list()[-1]
				img=cv2.resize(img,(900,500))
				cv2image = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA
				self.photo = Image.fromarray(cv2image)            # convert image for PIL
				imgtk = ImageTk.PhotoImage(image=self.photo)      # convert image for tkinter 
				self.panel1.imgtk = imgtk                         # anchor imgtk so it does not be deleted by garbage-collector  
				self.panel1.config(image=imgtk)                   # show the image
			except Exception as e:
				print("exception")
				
		self.vid1.release()
		#------------------------------------------------------------------------------------#
		
		#Read a frame from the IP camera
		#------------------------------------------------------------------------------------#
		ret, frame = cap.read()
		if ret:
			frame=cv2.resize(frame, (900, 500))
			
			#Apply the object detection model
			if(ObjectDetection==1):
				detection_service(frame)
				
			#Apply the image generated from the current frame to the specific panel
			cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)  # convert colors from BGR to RGBA
			self.photo = Image.fromarray(cv2image)              # convert image for PIL
			imgtk = ImageTk.PhotoImage(image=self.photo)        # convert image for tkinter 
			self.panel2.imgtk = imgtk                           # anchor imgtk so it does not be deleted by garbage-collector  
			self.panel2.config(image=imgtk)                     # show the image
		
		self.window.after(30, self.update)
 
def main(ip1,port1,ip2,ObjectDetectionFlag):
	global CREATE_NEW_OBJECTS_TYPE
	global DELETE_OBJECTS_TYPE
	global cap
	global net
	global CLASSES
	global COLORS
	global ObjectDetection
	
	ObjectDetection=ObjectDetectionFlag
	
	#This is the object detection model initialization
	#--------------------------------------------------------------------------------#
	if(ObjectDetection==1):
		CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
		"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
		"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
		"sofa", "train", "tvmonitor"]
		COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))


		# load our serialized model from disk
		print("[INFO] loading model...")
		net = cv2.dnn.readNetFromCaffe("MobileNetSSD_deploy.prototxt","MobileNetSSD_deploy.caffemodel")
	#--------------------------------------------------------------------------------#
	
	#Create a tcp socket in order to get the Pyro ids from the server
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_address = (ip1,port1)
	sock.connect(server_address)
	
	#Send a CREATE_NEW_OBJECTS_TYPE type message in order to receive the pyro ids from the server
	message = CREATE_NEW_OBJECTS_TYPE
	message=pickle.dumps(message)
	sock.sendall(message)
	
	object_id1 = sock.recv(10000)
	object_id1=pickle.loads(object_id1)
	#Data contains the pyro id
	print(object_id1[0])
	sock.close()
	
	#Create the proxy object
	EdgeMonitoringDevice = Pyro4.Proxy(object_id1[0])
	#Call start capture function. The skeleton will open the camera and will capture the video
	EdgeMonitoringDevice.start_capture()
	
	#connect with the IP camera
	#-------------------------------------------------------------------------------#
	cap = cv2.VideoCapture("rtsp://admin:camera1@"+ip2+":554//h264Preview_01_sub")
	if (cap.isOpened() == False): 
		print("Unable to read camera feed")
	#-------------------------------------------------------------------------------#
	
	#Create an object of the App class. Pass the Pyro proxies as arguments
	obj=App(Tk(),"Tkinter and OpenCV",EdgeMonitoringDevice)
	
	print("Waiting threads to return")
	#Wait for the threads to return
	obj.thread1.join()
	print("Thread 1 returned")
	#obj.thread2.join()
	#print("Thread 2 returned")
	
	#Create a tcp socket in order to inform the server side that the proxies will not exist anymore
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_address = (ip1,port1)
	sock.connect(server_address)
	
	#Send a DELETE_OBJECTS_TYPE type message in order to inform the server side that the proxies will not exist anymore
	message = DELETE_OBJECTS_TYPE
	message=pickle.dumps(message)
	sock.sendall(message)
	sock.close()

if __name__=="__main__":
    
	if(len(sys.argv)<5):
		print("Wrong number of arguments. Please give the ip address of the first server as a first argument, the port of the first server as a second argument, the ip of the first ip camera as a third argument and the Object Detection flag as a fourth argument")
		exit()
	
	main(sys.argv[1],int(sys.argv[2]),sys.argv[3],int(sys.argv[4]))


