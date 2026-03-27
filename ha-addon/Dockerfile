# Build from repo root: docker build -f ha-addon/Dockerfile .
ARG BUILD_VERSION=dev
FROM python:3.12-slim

WORKDIR /app
COPY mcp-server/ .
RUN pip install --no-cache-dir -e .

ENV DATA_DIR=/data
EXPOSE 8765

LABEL \
    io.hass.name="Garden Planner" \
    io.hass.description="A local-first, AI-native garden journal" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION}

CMD ["garden-planner"]
