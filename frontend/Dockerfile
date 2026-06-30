# Build stage
FROM node:20-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage — serve built assets via nginx
FROM nginx:alpine

# Copy built React app
COPY --from=build /app/dist /usr/share/nginx/html

# nginx.conf is mounted from the nginx service in docker-compose
# This default conf is used when the frontend container runs standalone
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
