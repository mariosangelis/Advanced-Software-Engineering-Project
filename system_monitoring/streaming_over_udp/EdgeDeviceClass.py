import Pyro4
import os 
import cv2
import time
import threading
import socket
import pickle
import math
import struct

MAX_DGRAM = 2**16
udp_streamer_mtx = threading.Lock()
POLL_UDP_STREAM_SOCKET=3
stream_port=30000

#Class to break down image frame segment if the size of image exceed maximum datagram size 
class FrameSegment():
	global MAX_DGRAM
	
	# extract 64 bytes in case UDP of frame overflow
	MAX_IMAGE_DGRAM = MAX_DGRAM - 64 
	
	#This is the constructor of the class
	def __init__(self,sock,addr):
		self.s = sock
		self.addr = addr
	
	#Compress image and Break down into data segments 
	def udp_frame(self, img):
		
		compress_img = cv2.imencode('.jpg', img)[1]
		dat = compress_img.tostring()
		size = len(dat)
		count = math.ceil(size/(self.MAX_IMAGE_DGRAM))
		array_pos_start = 0
		while count:
			array_pos_end = min(size, array_pos_start + self.MAX_IMAGE_DGRAM)
			self.s.sendto(struct.pack("B", count) +dat[array_pos_start:array_pos_end],self.addr)
			array_pos_start = array_pos_end
			count -= 1

        
@Pyro4.expose
class EdgeMonitoringDevice():

	#This is the constructor of the EdgeMonitoringDevice class
	def __init__(self,camera_path,lan_ip,wan_ip):
		self.lan_ip=lan_ip
		self.wan_ip=wan_ip
		self.camera_path=camera_path
		self.lock=threading.Lock()
		self.destroy_flag=0
		
	def get_wan_ip(self):
		return self.wan_ip
	
	def capture_function(self):
		
		global MAX_DGRAM
		global udp_streamer_mtx
		global POLL_UDP_STREAM_SOCKET
		global stream_port
		
		#Create a VideoCapture object
		#For example, camera_path is "/dev/v4l/by-id/usb-AONI_ELECTRONIC_CO.LTD_Canyon_CNS-CWC5_Webcam_20190322001-video-index0"
		#If a device has only one camera, we can use 0 as a camera_Path
		cap = cv2.VideoCapture(self.camera_path)

		# Check if camera opened successfully
		if (cap.isOpened() == False): 
			print("Unable to read camera feed")
			return -1

		# Default resolutions of the frame are obtained.The default resolutions are system dependent.
		# We convert the resolutions from float to integer.
		frame_width = int(cap.get(3))
		frame_height = int(cap.get(4))
		
		#Create a udp socket in order to stream the video and bind to the specific address
		udp_stream_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		stream_address = (self.lan_ip,stream_port)
		print("Server address is ",stream_address)
		udp_stream_socket.bind(stream_address)
		
		#Wait for client to poll the udp socket
		print("Wait for client to poll the udp socket")
		while(True):
			data, addr = udp_stream_socket.recvfrom(1024)
			data=pickle.loads(data)
			if (data==POLL_UDP_STREAM_SOCKET):
				print("Tkinter is on, start streaming")
				break
			else:
				print("Invalid command")
		
		#Initialize the frame cropper-sender
		fs = FrameSegment(udp_stream_socket,addr)
		
		while (cap.isOpened()):
			self.lock.acquire()
			#If destroy_flag is 1, then close the out instance and also close the camera
			if(self.destroy_flag==1):
				print("DESTROY THREAD")
				cap.release()
				self.lock.release()
				return()
			self.lock.release()
			
			#Read a frame, crop it and stream it using the udp stream socket
			ret, frame = cap.read()
			fs.udp_frame(frame)
			
	#This is the first method called by the proxy
	def start_capture(self):
		global udp_streamer_mtx
		
		#When the proxy calls this function, a thread is created in order to open the camera and to start capturing the video
		self.threadServer = threading.Thread(target=self.capture_function, args=())
		self.threadServer.start()
		return
	
	
	#This function is called from the proxy in order to inform the skeleton that the proxy object will not exist anymore
	def end_capture(self):
		print("Close capture device")
		
		self.lock.acquire()
		#Set the destroy_flag to 1. The thread will see this flag and it will terminate
		self.destroy_flag=1
		self.lock.release()
		print("Wait for my thread to terminate")
		#Wait for the thread to terminate
		self.threadServer.join()
		print("My thread returned")
		return()


