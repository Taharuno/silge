FROM node:20-alpine

WORKDIR /app

# Bağımlılıkları kur
COPY package*.json ./
RUN npm install

# Uygulama dosyaları
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
