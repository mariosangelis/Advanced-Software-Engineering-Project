from EdgeDeviceClass import *
import threading
import time
import socket
import sys
import pickle
Daemon=0

def remote_server_function(ip,port):
	global Daemon
	
	#Create a tcp socket 
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_address = (ip,port)
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
		
		file_output="outpy.avi"
		
		if(data==1):
			#Client just sent a CREATE_NEW_OBJECTS_TYPE message
			#Create an EdgeMonitoringDevice object and register it to Pyro
			#The first argument is the id of each camera and the second argument is the name of the video file in which the data from the specific camera will be stored
			object_id = Daemon.register(EdgeMonitoringDevice(0,file_output))
			print(object_id)
			
			#Send the id of the EdgeMonitoringDevice objects to the client
			data=[object_id]
			data=pickle.dumps(data)
			connection.sendall(data)
		else:
			#Client just sent a DELETE_OBJECTS_TYPE message
			print("Delete skeleton objects")
			#Daemon.disconnect(object_id)
			#Daemon.disconnect(object_id2)
			

def main(ip,port,wan_ip):
	
	global Daemon
	#Create a daemon instance. Set also the nat ip and the nat port for port forwarding purposes
	Daemon = Pyro4.Daemon(host=ip,port=port+1, nathost=wan_ip, natport=port+1)
	
	#Create a thread for the server-client communication
	thread1 = threading.Thread(target=remote_server_function, args=[ip,port])
	thread1.start()
	
	Daemon.requestLoop()

if __name__=="__main__":
	
	if(len(sys.argv)<4):
		print("Wrong number of arguments. Please give the ip address of the server as a first argument, the port of the server as a second argument and the WAN ip address as a third argument")
		exit()
		
	main(sys.argv[1],int(sys.argv[2]),sys.argv[3])

	
