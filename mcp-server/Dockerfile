FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .

ENV DATA_DIR=/data
VOLUME /data

EXPOSE 8765

CMD ["garden-planner"]
