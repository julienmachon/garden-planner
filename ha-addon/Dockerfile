# Build from repo root: docker build -f ha-addon/Dockerfile .
ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip

# Install mcp-server package (build context must be repo root)
COPY mcp-server/ /app/
RUN pip3 install --no-cache-dir --break-system-packages /app/

# s6-overlay service scripts
COPY ha-addon/rootfs /
RUN chmod a+x \
    /etc/services.d/garden-planner/run \
    /etc/services.d/garden-planner/finish

LABEL \
    io.hass.name="Garden Planner" \
    io.hass.description="A local-first, AI-native garden journal" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION}
