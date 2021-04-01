----------------------------------------------------------------------------------------------------------------------------------------------------------
With Balena service
%%%%%%%%%%%%%%%%%%%%% Raspberry Pi %%%%%%%%%%%%%%%%%%%%%

1) Connect to balena cloud 
   username: mariosag14@gmail.com
   password: mariosangelis1234
   
   
2) Start a terminal session to main process

3) Type: curl ifconfig.me in order to find your public (WAN) IP address

4) Start the Seleton service by typing: python3 Skeleton.py <Raspberry pi IP> <Raspberry Pi port> <WAN IP>
   ex: python3 Skeleton.py 192.168.1.3 12000 79.107.33.39
   
%%%%%%%%%%%%%%%%%%%%% Local host %%%%%%%%%%%%%%%%%%%%%

1) Type: python3 Tkinter.py --help in order to see the syntax of the arguments

2) Open a terminal and type the following command:

   python3 Tkinter.py --remote_camera <ip1> <p1> <ip2> <p2> ... --ip_camera <ip1> <ip2> ... --object_detection 0
   ex: python3 Tkinter.py --remote_camera 192.168.1.3  12000 --ip_camera 192.168.1.5  --object_detection 0   ----> same LAN
   ex: python3 Tkinter.py --remote_camera 79.107.33.39 12000 --ip_camera 79.107.33.39 --object_detection 0   ----> other LAN

----------------------------------------------------------------------------------------------------------------------------------------------------------
Without Balena service
   
%%%%%%%%%%%%%%%%%%%%% Raspberry Pi %%%%%%%%%%%%%%%%%%%%%
   
1) ifconfig

2) sudo nmap -sn 192.168.1.0/24

3) ssh ubuntu@<Raspberry Pi IP>

4) Start the Seleton service by typing: python3 Skeleton.py <Raspberry pi IP> <Raspberry Pi port> <WAN IP>
   ex: python3 Skeleton.py 192.168.1.3 12000 79.107.33.39

%%%%%%%%%%%%%%%%%%%%% Local host %%%%%%%%%%%%%%%%%%%%%

1) Type: python3 Tkinter.py --help in order to see the syntax of the arguments

2) Open a terminal and type the following command:

   python3 Tkinter.py --remote_camera <ip1> <p1> <ip2> <p2> ... --ip_camera <ip1> <ip2> ... --object_detection 0
   ex: python3 Tkinter.py --remote_camera 192.168.1.3  12000 --ip_camera 192.168.1.5  --object_detection 0   ----> same LAN
   ex: python3 Tkinter.py --remote_camera 79.107.33.39 12000 --ip_camera 79.107.33.39 --object_detection 0   ----> other LAN
