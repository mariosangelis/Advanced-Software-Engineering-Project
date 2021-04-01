FROM balenalib/raspberrypi3-python

COPY ./EdgeDeviceClass.py /
COPY ./Skeleton.py /
COPY ./opencv ./opencv
RUN ls
RUN cd opencv/build

RUN pip3 install Pyro4 && apt-get update -y && apt-get update && apt-get install cmake -y && apt-get install gcc g++ -y \
&& apt-get install libavcodec-dev libavformat-dev libswscale-dev -y \
&& apt-get install libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev -y \
&& apt-get install libgtk-3-dev -y \
&& apt-get install libpng-dev -y \
&& apt-get install libjpeg-dev -y \
&& apt-get install libopenexr-dev -y \
&& apt-get install libtiff-dev -y \
&& apt-get install libwebp-dev -y \
&& apt-get install python3-dev python3-numpy -y

RUN pip3 install numpy
RUN cd opencv/build && cmake ../ && ls && make && make install

#Give receiver_port by command line
ENTRYPOINT ["python3", "./Skeleton1.py","0.0.0.0","10000"]
