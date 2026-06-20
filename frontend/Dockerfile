FROM node:22-alpine AS deps

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder

WORKDIR /app

ARG BACKEND_API_URL=http://api:8000
ENV BACKEND_API_URL=${BACKEND_API_URL}

COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./

RUN npm run build
RUN npm prune --omit=dev

FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    BACKEND_API_URL=http://api:8000

COPY --from=builder /app ./

EXPOSE 3000

CMD ["npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000"]
