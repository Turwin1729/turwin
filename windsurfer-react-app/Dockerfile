FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 1723

ENV PORT=1723

CMD ["npm", "start"]
