FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instala dependências, Google Chrome e o ChromeDriver correspondente
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Ferramentas essenciais
    curl \
    gnupg \
    wget \
    unzip \
    xvfb \
    # Dependências essenciais para o Chrome/ChromeDriver funcionar
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxrandr2 \
    fonts-liberation \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    && mkdir -p /etc/apt/keyrings \
    # Adiciona o repositório do Google Chrome
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    # Instala o Chrome
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    # Instala o ChromeDriver compatível
    && CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1-3) \
    && echo "Chrome Version: $CHROME_VERSION" \
    && CHROME_DRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION%%.*}") \
    && echo "ChromeDriver Version: $CHROME_DRIVER_VERSION" \
    && wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chown root:root /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    # Cria link simbólico para o Chrome no local esperado
    && ln -sf /usr/bin/google-chrome /usr/bin/google-chrome-stable \
    # Limpeza
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/

RUN mkdir -p /app/downloads && chmod -R 777 /app/downloads

CMD ["python", "main.py"]