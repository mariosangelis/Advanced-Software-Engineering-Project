#THIS IS ONLY FOR LAN MONITORING

%%%%%%%%%%%%%%%%%%%%% Raspberry Pi %%%%%%%%%%%%%%%%%%%%%

1) Connect to the Raspberry Pi
   ssh ubuntu@192.168.1.3
   
2) Start the Seleton service by typing: python3 Skeleton.py <Raspberry pi LAN IP> <Raspberry Pi port> <WAN IP>
   ex: python3 Skeleton.py 192.168.1.3 12000 79.107.33.39
   
%%%%%%%%%%%%%%%%%%%%% Local host %%%%%%%%%%%%%%%%%%%%%

1) Open a terminal and type the following command:

   python3 Tkinter.py <Raspberry pi ip> <Raspberry pi port> <IP camera address> <Object_detection_flag>
   ex: python3 Tkinter.py 192.168.1.3 12000 192.168.1.5 0     ----> same LAN
   ex: python3 Tkinter.py 79.107.33.39 12000 79.107.33.39 0   ----> other LAN
