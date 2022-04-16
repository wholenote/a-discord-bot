FROM python:3.8.5-slim

WORKDIR /a-discord-bot

RUN apt-get update && \
    apt-get -y install gcc

RUN apt-get -y install ffmpeg

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]