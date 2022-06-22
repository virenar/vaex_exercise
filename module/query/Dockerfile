FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y \
            procps \
            libncurses5-dev \
            libbz2-dev \
            liblzma-dev \
            zlib1g-dev \
            gcc \
            make \
            bzip2

RUN apt-get update && apt-get install -y \
            procps

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

RUN mkdir -p /scripts
COPY ./scripts /scripts

WORKDIR /
ENV PATH "$PATH:/scripts"
