FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source files
COPY . .

# Build with more verbose output
RUN npm run build
RUN echo "Build complete. Contents of /app/build:" && \
    ls -la /app/build && \
    echo "Contents of /app/build/static (if exists):" && \
    ls -la /app/build/static || echo "No static directory found" && \
    echo "Contents of /app:" && \
    ls -la /app

# Stage 2: Serve
FROM nginx:alpine

# Copy build files
COPY --from=builder /app/build /usr/share/nginx/html/

# Verify files were copied
RUN echo "Contents of /usr/share/nginx/html:" && \
    ls -la /usr/share/nginx/html && \
    echo "Checking for index.html:" && \
    cat /usr/share/nginx/html/index.html || echo "index.html not found!"

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
