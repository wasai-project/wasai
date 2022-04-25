FROM ubuntu:18.04
From python:3.6.9

RUN apt update && \
    apt install -y software-properties-common sudo curl wget python vim libncurses5 psmisc libusb-1.0-0 && \
    rm -rf /*.deb /var/lib/apt/lists/* 

RUN mkdir -p /home/szh/LOGS && \
    mkdir -p /home/szh/wasai

COPY . /home/szh/wasai

WORKDIR /home/szh/wasai

RUN mv ./instrumentation/* /usr/bin/ && \
    python3 -m pip install -r ./requirements.txt

ENTRYPOINT ["/bin/bash"]