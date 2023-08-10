# pull official LTS base image
FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKER 1

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get install -y build-essential
RUN apt-get install -y git
RUN add-apt-repository ppa:ubuntugis/ppa
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update

# install gdal
RUN apt install -y gdal-bin libgdal-dev

# Install py39 from deadsnakes repository
RUN apt-get install -y python3.9
RUN apt-get install -y python3.9-dev
RUN apt-get install -y python3-pip

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install --force git+https://github.com/scikit-learn-contrib/hdbscan.git
RUN pip install -r requirements.txt

# copy project
COPY . .
