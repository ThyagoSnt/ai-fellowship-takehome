# === Stage 1: Build ===
FROM node:20-alpine AS builder
WORKDIR /app

# Install
RUN npm install -g pnpm@9
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# === Stage 2: Runtime ===
FROM node:20-alpine
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm@9

# Coping built files from the builder stage
COPY --from=builder /app ./

EXPOSE 3000
CMD ["pnpm", "start"]