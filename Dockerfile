FROM ubuntu:18.04
From python:3.6.9

RUN apt update && \
    apt install -y software-properties-common sudo curl wget python vim libncurses5 psmisc libusb-1.0-0 && \
    rm -rf /*.deb /var/lib/apt/lists/* 



# RUN useradd --create-home szh && usermod -aG sudo szh  && \
#     echo 'szh:' | chpasswd
# RUN usermod -u 1000 szh && usermod -G 1000 szh


# RUN  useradd admin && echo "admin:admin" | chpasswd && adduser admin sudo
# USER admin




RUN mkdir -p /home/szh/LOGS && \
    mkdir -p /home/szh/wasai

COPY . /home/szh/wasai

WORKDIR /home/szh/wasai

RUN mv ./instrumentation/* /usr/bin/ && \
    python3 -m pip install -r ./requirements.txt

# RUN python3 -m venv ./venv && source ./venv/bin/activate
# RUN python3 -m pip install -r requirements.txt


ENTRYPOINT ["/bin/bash"]
# python3 -m bin.fuzz ./examples/batdappboomx/batdappboomx.wasm ./examples/batdappboomx/batdappboomx.abi batdappboomx 120 1000 ./rt/


# git, make, bzip2, automake, libbz2-dev, libssl-dev, doxygen, graphviz, libgmp3-dev, autotools-dev,libicu-dev, python2.7, python2.7-dev, python3, python3-dev, autoconf, libtool, curl, zlib1g-dev, sudo, ruby, libusb-1.0-0-dev, libcurl4-gnutls-dev, pkg-config, patch