FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libasound2-dev \
    pulseaudio \
    libmodplug1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install gunicorn

COPY . .

ENV HF_SPACE_HEALTH_PATH=/health
ENV PORT=8080
ENV MPLCONFIGDIR=/tmp
ENV SDL_AUDIODRIVER=pulseaudio

EXPOSE 8080

RUN echo '#!/bin/bash\n\
pulseaudio --start --exit-idle-time=-1\n\
exec gunicorn -w 1 --timeout 120 -b 0.0.0.0:$PORT app:app' > entrypoint.sh && chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
