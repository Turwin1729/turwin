FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source files
COPY . .

# Build with more verbose output
RUN DISABLE_ESLINT_PLUGIN=true CI=true npm run build && \
    echo "Build complete. Contents of /app/build:" && \
    ls -la /app/build

# Stage 2: Serve
FROM nginx:alpine

# Copy build files and nginx config
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    echo "Final contents of /usr/share/nginx/html:" && \
    ls -la /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
