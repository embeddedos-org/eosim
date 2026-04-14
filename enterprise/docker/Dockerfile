FROM python:3.12-slim AS base
LABEL maintainer="embeddedos-org" description="Simulation Server — EoS Enterprise"

WORKDIR /app
COPY pyproject.toml setup.cfg* setup.py* ./
COPY eosim/ eosim/
COPY platforms/ platforms/
RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
CMD ["python", "-m", "eosim.cli.main"]
