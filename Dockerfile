FROM python:3.8.12-bullseye

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y unzip

ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/chrome

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r ./requirements.txt