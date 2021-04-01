FROM balenalib/raspberrypi3-python
WORKDIR ./
COPY ./EdgeDeviceClass.py /
COPY ./Skeleton.py /
COPY ./opencv /opencv
RUN cd ./opencv && mkdir build

RUN /usr/local/bin/python3.9 -m pip install --upgrade pip && pip3 install Pyro4 && apt-get update \
&& apt-get install cmake -y && apt-get install gcc g++ -y \
&& apt-get install make \
&& apt-get install libavcodec-dev libavformat-dev libswscale-dev -y \
&& apt-get install libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev -y \
&& apt-get install libgtk-3-dev -y \
&& apt-get install libpng-dev -y \
&& apt-get install libjpeg-dev -y \
&& apt-get install libopenexr-dev -y \
&& apt-get install libtiff-dev -y \
&& apt-get install libwebp-dev -y \
&& apt-get install python3-dev python3-numpy -y \
&& pip3 install numpy && pip3 install --upgrade numpy

RUN cd opencv/build && cmake -D BUILD_NEW_PYTHON_SUPPORT=ON \
-D BUILD_opencv_python3=ON \
-D HAVE_opencv_python3=ON \
-D PYTHON_DEFAULT_EXECUTABLE=/usr/bin/python3 ../ && ls && make && make install

#Give receiver_port by command line
ENTRYPOINT ["/bin/sh"]
