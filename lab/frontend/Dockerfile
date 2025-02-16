FROM node:18-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build && ls -la build/

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
RUN ls -la /usr/share/nginx/html && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
