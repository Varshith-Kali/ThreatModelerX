FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    default-jre \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g retire

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN curl -L https://github.com/spotbugs/spotbugs/releases/download/4.8.3/spotbugs-4.8.3.tgz | tar xz -C /opt/

ENV SPOTBUGS_HOME=/opt/spotbugs-4.8.3
ENV PATH="${PATH}:${SPOTBUGS_HOME}/bin"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
