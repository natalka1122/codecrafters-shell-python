FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Install packages
RUN apt update && \
    apt install -y python3 python3-pip python3-venv git python-is-python3 iputils-ping net-tools telnet tcpdump redis-tools netcat-openbsd && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --upgrade  argcomplete mypy pytest pytest-cov pytest-asyncio black wemake-python-styleguide cohesion dlint pytest-xdist vulture isort jupyter pipenv

# Install Codecrafters Python
RUN curl https://codecrafters.io/install.sh | sh
