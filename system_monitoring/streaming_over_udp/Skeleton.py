from __future__ import division
from EdgeDeviceClass import *
import cv2
import numpy as np
import socket
import struct
import math
import threading
import time
import sys
import pickle

Daemon=0
CREATE_NEW_OBJECTS_TYPE=1
DELETE_OBJECTS_TYPE=2

def remote_server_function(lan_ip,port,wan_ip):
	global Daemon
	global CREATE_NEW_OBJECTS_TYPE
	global DELETE_OBJECTS_TYPE
	
	#Create a tcp socket 
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_address = (lan_ip,port)
	sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
	sock.bind(server_address)
	sock.listen(12)
	print("Waiting for connections")
	
	#Waiting for connections
	while(True):
		#Accept a connection
		connection, address = sock.accept()
		data = connection.recv(1000)
		data=pickle.loads(data)
		
		if(data==CREATE_NEW_OBJECTS_TYPE):
			#Client just sent a CREATE_NEW_OBJECTS_TYPE message
			#Create 2 EdgeMonitoringDevice objects and register them to Pyro
			#The first argument is the id of the camera, the second argument is LAN IP address and the third argument is the WAN IP address
			object_id = Daemon.register(EdgeMonitoringDevice(0,lan_ip,wan_ip))
			print(object_id)
			
			#Send the id of the EdgeMonitoringDevice object to the client
			data=[object_id]
			data=pickle.dumps(data)
			connection.sendall(data)
		elif(data==DELETE_OBJECTS_TYPE):
			#Client just sent a DELETE_OBJECTS_TYPE message
			print("Delete skeleton objects")
			#Daemon.disconnect(object_id)
			#Daemon.disconnect(object_id2)
			

def main(lan_ip,port,wan_ip):
	
	global Daemon
	#Create a Daemon instance. Set also the nat ip and the nat port for port forwarding purposes
	Daemon = Pyro4.Daemon(host=lan_ip,port=port+1, nathost=wan_ip, natport=port+1)
	
	#Create a thread for the server-client communication
	thread1 = threading.Thread(target=remote_server_function, args=[lan_ip,port,wan_ip])
	thread1.start()
	
	Daemon.requestLoop()


if __name__=="__main__":
	
	if(len(sys.argv)<4):
		print("Wrong number of arguments. Please give the ip address of the server as a first argument, the port of the server as a second argument and the WAN ip address as a third argument")
		exit()
		
	main(sys.argv[1],int(sys.argv[2]),sys.argv[3])

	
