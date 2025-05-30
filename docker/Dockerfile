# docker/Dockerfile
FROM python:3.12-slim AS runner

USER root

ENV http_proxy=${HTTP_PROXY:-}
ENV https_proxy=${HTTPS_PROXY:-}
ENV docker=1

WORKDIR /app

COPY requirements-docker.txt .

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libnss3 \
    libgconf-2-4 \
    libxi6 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    libglib2.0-0 \
    fonts-liberation \
    libappindicator3-1 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    git \
 && rm -rf /var/lib/apt/lists/*

# 安装 Chrome（官方稳定版）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# 安装 ChromeDriver（确保版本匹配）
RUN set -eux; \
    JSON_URL="https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"; \
    DRIVER_URL=$(curl -s $JSON_URL | \
        python3 -c "import sys, json; \
        j=json.load(sys.stdin); \
        print(j['channels']['Stable']['downloads']['chromedriver'][0]['url'])"); \
    wget -O /tmp/chromedriver.zip "$DRIVER_URL"; \
    unzip /tmp/chromedriver.zip -d /tmp/; \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver; \
    chmod +x /usr/local/bin/chromedriver; \
    rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64


RUN apt-get install -y git

RUN pip install --no-cache-dir -r requirements-docker.txt

COPY . .

# CMD ["python", "run_judge.py"]
#RUN python run_judge.py
#
#FROM scratch AS output
#
#COPY --from=runner /app/experiments/ /experiments/