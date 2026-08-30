# Multi-stage Dockerfile for GCP RF Telemetry Collector Agent

FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ src/
COPY proto/ proto/
COPY scripts/ scripts/

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir . grpcio-tools
RUN python scripts/compile_proto.py

# Final runtime image
FROM python:3.12-slim as runner

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

COPY src/ src/
COPY data/ data/

EXPOSE 8080

ENTRYPOINT ["python", "-m", "agent.cli"]
CMD ["--csv-file", "data/sample_rf.csv", "--port", "8080"]
