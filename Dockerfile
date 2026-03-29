FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
ENV TTS_CACHE_DIR=/app/cache
RUN mkdir -p /app/cache
EXPOSE 5111
CMD ["python", "server.py"]
