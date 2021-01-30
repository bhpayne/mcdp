# Use baseimage-docker which is a modified Ubuntu specifically for Docker
# https://hub.docker.com/r/phusion/baseimage
# https://github.com/phusion/baseimage-docker
FROM phusion/baseimage:bionic-1.0.0

# Use baseimage-docker's init system
CMD ["/sbin/my_init"]

# Update and install packages
#RUN apt update && apt -y upgrade && apt -y install \
RUN apt-get update && apt -y install \
	python3 \
        python3-pip \
        python \
        python-pip \
        git

COPY . /opt/

WORKDIR /opt/

# I am unable to get this working -- 
# python3 fails on https://github.com/AndreaCensi/compmake/tree/master/src/compmake
# python2 fails on "watchdog" due to "ImportError: No module named util"
RUN pip install -r requirements.txt
