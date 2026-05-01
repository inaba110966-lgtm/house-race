FROM node:20-alpine AS builder

WORKDIR /app/frontend
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

# ビルド成果物のみをエクスポート (マルチステージ参照用)
FROM scratch AS export
COPY --from=builder /app/frontend/dist /dist
