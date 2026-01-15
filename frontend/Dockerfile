FROM node:20-alpine

WORKDIR /app

# Копируем package.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm install

# Копируем код
COPY . .

# Expose порт
EXPOSE 3000

# Запуск dev сервера
CMD ["npm", "start"]
