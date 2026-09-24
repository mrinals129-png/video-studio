FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# Shared libraries needed by the renderer's downloaded Chromium browser.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 \
    libxrandr2 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
