FROM ubuntu:14.10
MAINTAINER Aexea Carpentry

ENV DEBIAN_FRONTEND noninteractive

# Set the locale
RUN locale-gen en_US.UTF-8  
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8  

RUN apt-get update && apt-get upgrade -y -o DPkg::Options::=--force-confold &&\
    apt-get install -y python-pip python-dev

EXPOSE 8000

RUN pip install saltobserver==0.9.2

ADD config.py /config.py
ENV SALTOBSERVER_SETTINGS /config.py

CMD run_saltobserver -b 0.0.0.0:8000
