# pull official LTS base image
FROM ubuntu:20.04

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKER 1

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:ubuntugis/ppa
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update

# install gdal
RUN apt install -y gdal-bin libgdal-dev

# Install py39 from deadsnakes repository
RUN apt-get install -y python3.9
RUN apt-get install -y python3-pip

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .
