FROM python:3.8.12-bullseye

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y unzip

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]