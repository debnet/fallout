FROM python:latest
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install -y gettext
RUN mkdir -p /rpg
ADD requirements.txt /rpg
RUN pip install --force --upgrade pip
RUN pip install --force -r rpg/requirements.txt
ADD . /rpg
WORKDIR /rpg
