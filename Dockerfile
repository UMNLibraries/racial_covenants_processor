# pull official LTS base image
FROM ubuntu:24.04
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
# RUN add-apt-repository ppa:ubuntugis-unstable/ppa
RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable
# RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update

# install gdal
RUN apt install -y gdal-bin libgdal-dev

# Install py311 from deadsnakes repository
# RUN apt-get install -y python3.12
RUN apt-get install -y python3.12-dev
# RUN apt-get install -y python3-pip
RUN apt-get install -y python3.12-venv

# Virtual python environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install dependencies
# RUN pip install --upgrade pip  # With v 24 of pip lots of requirements inside dependencies will break. So don't force upgrade for now.
COPY ./requirements.txt .
# RUN pip install --force git+https://github.com/scikit-learn-contrib/hdbscan.git
RUN pip install -r requirements.txt

# copy project
COPY . .
