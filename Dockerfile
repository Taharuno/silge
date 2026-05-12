FROM python:3.12-slim

WORKDIR /app

# Sistem bağımlılıkları + saat dilimi
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    tzdata \
    && ln -sf /usr/share/zoneinfo/Europe/Istanbul /etc/localtime \
    && echo "Europe/Istanbul" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY . .

# Klasörleri oluştur
RUN mkdir -p tutanaklar uploads data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
