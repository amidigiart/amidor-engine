FROM python:3.12-slim

WORKDIR /app

# ffmpeg: pregatit pentru STT local (whisper) la nevoie; piper se monteaza separat
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn pydantic numpy cryptography \
    && pip install --no-cache-dir "ukbe-core @ git+https://github.com/amidigiart/ukbe-core@main"

COPY *.py ./
COPY static/ static/
COPY monitor/ monitor/

ENV AMIDOR_ENV=prod
EXPOSE 8124
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8124"]
